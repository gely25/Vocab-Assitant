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

    # Si es una frase (contiene espacios)
    if " " in text:
        translation = TranslationService.translate(text, target_lang=target_lang, source_lang=source_lang)
        return JsonResponse({
            'type': 'phrase',
            'original': text,
            'translation': translation,
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
        'phonetic': None,
        'meanings': []
    }

    if definition_data:
        response_data.update(definition_data)

    return JsonResponse(response_data)


def save_word(request):
    """Guarda una palabra en las flashcards"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    word = body.get('word', '').strip()
    translation = body.get('translation', '').strip() # CORRECCIÓN: Usar el valor del body
    
    if not word:
        return JsonResponse({'error': 'Palabra vacía'}, status=400)

    card, created = FlashcardService.create_flashcard(
        word=word,
        translation=translation,
        definition=body.get('definition', ''),
        example=body.get('example', ''),
        example_2=body.get('example_2', ''),
        synonyms=body.get('synonyms', ''),
        phonetic=body.get('phonetic', ''),
        source_lang=body.get('source_lang', 'en'), # Guardar idiomas
        target_lang=body.get('target_lang', 'es')
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
