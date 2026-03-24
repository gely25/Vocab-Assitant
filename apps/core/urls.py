from django.urls import path
from .views.home import home
from .views.api_views import define_word, save_word, ocr_upload
from .views.review_views import review_home, flashcards_due, review_action

app_name = 'core'

urlpatterns = [
    path('', home, name='home'),
    path('define/', define_word, name='define_word'),
    path('save/', save_word, name='save_word'),
    path('ocr/', ocr_upload, name='ocr_upload'),
    path('review/', review_home, name='review_home'),
    path('api/due/', flashcards_due, name='flashcards_due'),
    path('api/review/<int:card_id>/', review_action, name='review_action'),
]