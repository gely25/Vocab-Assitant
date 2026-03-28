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
