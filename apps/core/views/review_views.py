import json
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
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
                'synonyms': card.synonyms,
                'part_of_speech': card.part_of_speech,
                'category': card.category,
                'source_lang': card.source_lang,
                'target_lang': card.target_lang
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
    """API que devuelve estadísticas de aprendizaje para el nuevo dashboard"""
    try:
        # 1. Dashboard core stats
        stats = FlashcardService.get_dashboard_stats()
        
        # 2. Add detailed lists with timing for 'Mis Tarjetas' view
        now = timezone.now()
        all_cards = FlashcardService.get_all_flashcards()
        
        def format_timing(dt):
            diff = (dt.date() - now.date()).days
            if diff <= 0: return 'vence hoy'
            if diff == 1: return 'mañana'
            return f'en {diff} días'

        detailed_cards = []
        for c in all_cards:
            detailed_cards.append({
                'id': c.id,
                'word': c.word,
                'translation': c.translation,
                'status': 'dominated' if c.interval >= 21 else ('upcoming' if c.next_review > now else 'today'),
                'timing': format_timing(c.next_review)
            })
            
        stats['detailed_cards'] = detailed_cards
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

def ai_explore(request):
    """Explora a fondo una palabra usando diferentes herramientas de IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        body = json.loads(request.body)
        word = body.get('word', '').strip()
        action = body.get('action', 'chat').strip()
        context = body.get('context', '').strip()
        query = body.get('query', '').strip()
        source_lang = body.get('source_lang', 'en')
        target_lang = body.get('target_lang', 'es')
        
        if not word:
            return JsonResponse({'error': 'Falta la palabra'}, status=400)
            
        from ..services.ai_service import AIService
        
        if action == 'synonyms':
            result = AIService.get_synonyms(word, context, source_lang, target_lang)
        elif action == 'caution':
            result = AIService.get_usage_caution(word, source_lang, target_lang)
        elif action == 'etymology':
            result = AIService.get_etymology(word, target_lang)
        elif action == 'chat':
            result = AIService.chat_about_word(word, query or "Cuéntame más sobre esta palabra", source_lang, target_lang)
        elif action == 'examples':
            result = AIService.generate_examples(word, context, source_lang, target_lang)
        else:
            return JsonResponse({'error': 'Acción no válida'}, status=400)
            
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
