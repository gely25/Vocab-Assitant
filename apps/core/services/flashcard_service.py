from ..models import Flashcard
from .translation_service import TranslationService
from .dictionary_service import DictionaryService
from django.utils import timezone

class FlashcardService:
    @staticmethod
    def get_due_flashcards():
        """Retorna las flashcards que toca revisar hoy"""
        return Flashcard.objects.filter(next_review__lte=timezone.now())

    @staticmethod
    def create_flashcard(word, translation, definition='', example='', example_2='', synonyms='', phonetic='', source_lang='en', target_lang='es'):
        """Crea una flashcard si no existe duplicada"""
        if Flashcard.objects.filter(word__iexact=word).exists():
            return None, False
        
        card = Flashcard.objects.create(
            word=word,
            translation=translation,
            definition=definition,
            example=example,
            example_2=example_2,
            synonyms=synonyms,
            phonetic=phonetic,
            source_lang=source_lang,
            target_lang=target_lang
        )
        return card, True

    @staticmethod
    def review_card(card_id, quality):
        """Procesa la revisión de una flashcard"""
        try:
            card = Flashcard.objects.get(id=card_id)
            card.review(quality)
            return card, True
        except Flashcard.DoesNotExist:
            return None, False

    @staticmethod
    def get_flashcard_stats():
        """Retorna estadísticas y listas de flashcards por estado de calidad"""
        all_cards = Flashcard.objects.all()
        
        # Categorización por última calidad de respuesta
        dominated = all_cards.filter(last_quality=5)
        to_confirm = all_cards.filter(last_quality=3)
        pending = all_cards.exclude(last_quality__in=[3, 5])
        
        def safe_json(cards):
            return [
                {'id': c.id, 'word': c.word, 'translation': c.translation, 'repetitions': c.repetitions} 
                for c in cards
            ]

        return {
            'total': all_cards.count(),
            'pending_count': pending.count(),
            'to_confirm_count': to_confirm.count(),
            'dominated_count': dominated.count(),
            'pending_list': safe_json(pending),
            'to_confirm_list': safe_json(to_confirm),
            'dominated_list': safe_json(dominated),
        }

    @staticmethod
    def get_dashboard_stats():
        """Retorna estadísticas completas para el nuevo dashboard premium"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        all_cards = Flashcard.objects.all()
        
        # 1. Donut Chart Data
        due_today = all_cards.filter(next_review__lte=now).count()
        done_today = all_cards.filter(last_review_at__gte=today_start).count()
        
        total_session = due_today + done_today
        progress = int((done_today / total_session * 100)) if total_session > 0 else 100
        
        # 2. Status Bars
        next_3_days = all_cards.filter(
            next_review__gt=now, 
            next_review__lte=now + timezone.timedelta(days=3)
        ).count()
        
        dominated_count = all_cards.filter(interval__gte=21).count()
        
        # 3. Forecast histogram (Next 7 days)
        forecast = []
        for i in range(7):
            d_start = today_start + timezone.timedelta(days=i)
            d_end = d_start + timezone.timedelta(days=1)
            count = all_cards.filter(next_review__gte=d_start, next_review__lt=d_end).count()
            forecast.append({
                'day': d_start.strftime('%a'),
                'count': count,
                'full_date': d_start.strftime('%Y-%m-%d')
            })

        # 4. Streak Calculation (Simplificada)
        streak = 0
        check_date = today_start
        while True:
            day_reviews = all_cards.filter(
                last_review_at__gte=check_date, 
                last_review_at__lt=check_date + timezone.timedelta(days=1)
            ).exists()
            
            if day_reviews:
                streak += 1
                check_date -= timezone.timedelta(days=1)
            else:
                # Si hoy no ha repasado aún, probamos desde ayer para no romper la racha
                if check_date == today_start:
                    check_date -= timezone.timedelta(days=1)
                    continue
                break
            if streak > 365: break # Sanity check

        return {
            'session': {
                'done': done_today,
                'pending': due_today,
                'total': total_session,
                'progress': progress,
                'streak': streak
            },
            'categories': {
                'today': due_today,
                'upcoming': next_3_days,
                'dominated': dominated_count
            },
            'forecast': forecast,
            'total_cards': all_cards.count()
        }

    @staticmethod
    def get_reset_stats():
        """Limpia o devuelve estadísticas básicas (compatibilidad)"""
        return FlashcardService.get_flashcard_stats()

    @staticmethod
    def get_pending_flashcards():
        """Retorna todas las palabras que NO están dominadas (calidad < 5)"""
        return Flashcard.objects.exclude(last_quality=5)

    @staticmethod
    def get_all_flashcards():
        """Retorna todas las flashcards sin excepción"""
        return Flashcard.objects.all()

    @staticmethod
    def reset_flashcard(card_id):
        """Reinicia el progreso de una flashcard"""
        try:
            card = Flashcard.objects.get(id=card_id)
            card.repetitions = 0
            card.interval = 1
            card.ease_factor = 2.5
            card.last_quality = 0
            card.next_review = timezone.now()
            card.save()
            return True
        except Flashcard.DoesNotExist:
            return False
