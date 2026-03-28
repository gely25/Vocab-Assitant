import json
from django.http import JsonResponse
from ..services.translation_service import TranslationService
from ..services.dictionary_service import DictionaryService
from ..services.flashcard_service import FlashcardService
from ..services.ocr_service import OCRService

def ocr_upload(request):
    """Procesa una imagen y devuelve el texto extraído"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    image = request.FILES.get('image')
    lang = request.POST.get('lang', 'en') # Nuevo parámetro de idioma
    
    if not image:
        return JsonResponse({'error': 'No se proporcionó imagen'}, status=400)
    
    text = OCRService.extract_text(image, lang=lang)
    if text is None:
        return JsonResponse({'error': 'Fallo al procesar OCR (¿Tesseract instalado?)'}, status=500)
    
    return JsonResponse({'text': text})

def define_word(request):
    """Obtiene traducción y definición de una palabra o frase"""
    text = request.GET.get('word', '').strip()
    if not text:
        return JsonResponse({'error': 'No se proporcionó texto'}, status=400)
    
    source_lang = request.GET.get('source', 'en') # Idioma de origen
    target_lang = request.GET.get('target', 'es') # Idioma de destino

    # Normalizar espacios/saltos de línea ocultos
    import re
    text = re.sub(r'\s+', ' ', text).strip()

    pinyin_str = None
    if source_lang == 'zh-CN':
        try:
            from pypinyin import pinyin, Style
            pinyin_list = pinyin(text, style=Style.TONE)
            # pinyin() returns a list of lists: [['nǐ'], ['hǎo']]
            pinyin_str = " ".join([item[0] for item in pinyin_list])
        except ImportError:
            pass

    # Si es una frase (contiene espacios)
    if " " in text:
        translation = TranslationService.translate(text, target_lang=target_lang, source_lang=source_lang)
        return JsonResponse({
            'type': 'phrase',
            'original': text,
            'translation': translation,
            'phonetic': pinyin_str,
        })

    # Si es una palabra
    definition_data = DictionaryService.get_definition(text, lang=source_lang)
    translation = TranslationService.translate(text, target_lang=target_lang, source_lang=source_lang)

    response_data = {
        'type': 'word',
        'original': text,
        'translation': translation,
        'definition': None,
        'example': None,
        'phonetic': pinyin_str,
        'meanings': []
    }

    if definition_data:
        response_data.update(definition_data)
        
    if pinyin_str:
        response_data['phonetic'] = pinyin_str

    return JsonResponse(response_data)


def save_word(request):
    """Guarda una palabra en las flashcards"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        if not request.body:
            return JsonResponse({'error': 'Cuerpo de la petición vacío'}, status=400)
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido en petición'}, status=400)

    # Evitamos error si get devuelve None
    word = str(body.get('word') or body.get('original') or '').strip()
    translation = str(body.get('translation') or '').strip()
    
    if not word:
        return JsonResponse({'error': 'Falta la palabra original para guardar.'}, status=400)
        
    try:
        card, created = FlashcardService.create_flashcard(
            word=word,
            translation=translation,
            definition=str(body.get('definition') or ''),
            example=str(body.get('context') or body.get('example') or ''),
            example_2=str(body.get('example_2') or ''),
            synonyms=str(body.get('synonyms') or ''),
            phonetic=str(body.get('phonetic') or ''),
            source_lang=str(body.get('source_lang', 'en') or 'en'),
            target_lang=str(body.get('target_lang', 'es') or 'es')
        )

        if not created:
            return JsonResponse({
                'status': 'duplicate',
                'message': f'"{word}" ya está en tus flashcards'
            })

        return JsonResponse({
            'status': 'ok',
            'message': f'"{word}" guardado en flashcards ✓'
        })
    except Exception as e:
        print("Error saving flashcard:", e)
        return JsonResponse({'error': 'Error interno al guardar: ' + str(e)}, status=500)

def explain_context(request):
    """Explica el matiz y pronunciación de una palabra en su contexto"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        body = json.loads(request.body)
        word = body.get('word', '').strip()
        context = body.get('context', '').strip()
        source_lang = body.get('source_lang', 'en')
        target_lang = body.get('target_lang', 'es')
        
        if not word:
            return JsonResponse({'error': 'Palabra vacía'}, status=400)
            
        from ..services.ai_service import AIService
        result = AIService.explain_context(word, context, source_lang, target_lang)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_examples(request):
    """Genera ejemplos de uso cotidiano para una palabra"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        body = json.loads(request.body)
        word = body.get('word', '').strip()
        context = body.get('context', '').strip()
        source_lang = body.get('source_lang', 'en')
        target_lang = body.get('target_lang', 'es')
        
        if not word:
            return JsonResponse({'error': 'Palabra vacía'}, status=400)
            
        from ..services.ai_service import AIService
        result = AIService.generate_examples(word, context, source_lang, target_lang)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def launch_desktop_client(request):
    """Lanza el cliente de escritorio (solo funciona localmente)"""
    import subprocess
    import sys
    import os
    
    # Ruta absoluta al script
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(base_dir, 'desktop_client', 'main_app.py')
    
    try:
        command = [sys.executable, script_path]
        print(f"DEBUG: Intentando lanzar -> {' '.join(command)}")
        
        # Popen para no bloquear el proceso de Django
        process = subprocess.Popen(command, 
                         stdout=subprocess.DEVNULL, 
                         stderr=None, 
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        
        return JsonResponse({
            'status': 'ok', 
            'message': 'Asistente iniciado',
            'pid': process.pid
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
