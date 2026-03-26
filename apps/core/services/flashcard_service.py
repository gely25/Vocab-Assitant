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
