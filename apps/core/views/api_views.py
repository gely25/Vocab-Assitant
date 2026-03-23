import json
from django.http import JsonResponse
from ..services.translation_service import TranslationService
from ..services.dictionary_service import DictionaryService
from ..services.flashcard_service import FlashcardService

def define_word(request):
    """Obtiene traducción y definición de una palabra o frase"""
    text = request.GET.get('word', '').strip()
    if not text:
        return JsonResponse({'error': 'No se proporcionó texto'}, status=400)
    
    target_lang = request.GET.get('target', 'es')

    # Si es una frase (contiene espacios)
    if " " in text:
        translation = TranslationService.translate(text, target_lang=target_lang)
        return JsonResponse({
            'type': 'phrase',
            'original': text,
            'translation': translation,
        })

    # Si es una palabra
    definition_data = DictionaryService.get_definition(text)
    translation = TranslationService.translate(text, target_lang=target_lang)

    response_data = {
        'type': 'word',
        'original': text,
        'translation': translation,
        'definition': None,
        'example': None,
        'phonetic': None
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
        phonetic=body.get('phonetic', '')
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
