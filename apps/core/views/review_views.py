import json
from django.shortcuts import render
from django.http import JsonResponse
from ..services.flashcard_service import FlashcardService

def review_home(request):
    """Renderiza la página de repaso"""
    return render(request, 'core/review.html')

def flashcards_due(request):
    """API que devuelve las flashcards filtradas por modo"""
    try:
        mode = request.GET.get('mode', 'due')
        
        if mode == 'all':
            due_cards = FlashcardService.get_all_flashcards()
        elif mode == 'pending':
            due_cards = FlashcardService.get_pending_flashcards()
        else:
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
                'synonyms': card.synonyms
            })
        return JsonResponse({'flashcards': data, 'is_all_mode': mode == 'all'})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

def review_action(request, card_id):
    """Aplica el algoritmo SM-2 o simplemente registra un repaso extra"""
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

def flashcards_stats(request):
    """API que devuelve estadísticas de aprendizaje"""
    try:
        stats = FlashcardService.get_flashcard_stats()
        return JsonResponse(stats)
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

def reset_card(request, card_id):
    """Reinicia el progreso de una palabra"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    success = FlashcardService.reset_flashcard(card_id)
    if not success:
        return JsonResponse({'error': 'Flashcard no encontrada'}, status=404)
        
    return JsonResponse({'status': 'ok', 'message': 'Progreso reiniciado'})
