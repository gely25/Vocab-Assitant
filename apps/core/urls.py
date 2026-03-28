from django.urls import path
from .views.home import home, live_caption
from .views.api_views import (
    define_word, save_word, ocr_upload, explain_context, 
    generate_examples, launch_desktop_client
)
from .views.review_views import review_home, flashcards_due, review_action, flashcards_stats, reset_card

app_name = 'core'

urlpatterns = [
    path('', home, name='home'),
    path('live/', live_caption, name='live_caption'),
    path('api/launch/', launch_desktop_client, name='launch_desktop'),
    path('define/', define_word, name='define_word'),
    path('save/', save_word, name='save_word'),
    path('ocr/', ocr_upload, name='ocr_upload'),
    path('review/', review_home, name='review_home'),
    path('api/due/', flashcards_due, name='flashcards_due'),
    path('api/review/<int:card_id>/', review_action, name='review_action'),
    path('api/stats/', flashcards_stats, name='flashcards_stats'),
    path('api/reset/<int:card_id>/', reset_card, name='reset_card'),
    path('api/ai/explain/', explain_context, name='ai_explain'),
    path('api/ai/examples/', generate_examples, name='ai_examples'),
]