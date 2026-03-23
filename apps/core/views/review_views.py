import json
from django.shortcuts import render
from django.http import JsonResponse
from ..services.flashcard_service import FlashcardService

def review_home(request):
    """Renderiza la página de repaso"""
    return render(request, 'core/review.html')

def flashcards_due(request):
    """API que devuelve las flashcards pendientes para hoy"""
    due_cards = FlashcardService.get_due_flashcards()
    data = []
    for card in due_cards:
        data.append({
            'id': card.id,
            'word': card.word,
            'translation': card.translation,
            'definition': card.definition,
            'phonetic': card.phonetic,
            'example': card.example,
            'example_2': card.example_2,
            'synonyms': card.synonyms
        })
    return JsonResponse({'flashcards': data})

def review_action(request, card_id):
    """Aplica el algoritmo SM-2 según la calificación del usuario"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        body = json.loads(request.body)
        quality = int(body.get('quality', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Datos de revisión inválidos'}, status=400)

    card, success = FlashcardService.review_card(card_id, quality)

    if not success:
        return JsonResponse({'error': 'Flashcard no encontrada'}, status=404)

    return JsonResponse({
        'status': 'ok',
        'word': card.word,
        'next_review': card.next_review.strftime('%Y-%m-%d'),
        'interval': card.interval
    })
