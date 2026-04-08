from django.db import models
from django.utils import timezone

class Flashcard(models.Model):
    word = models.CharField(max_length=300)
    translation = models.CharField(max_length=300, blank=True)
    definition = models.TextField(blank=True)
    example = models.TextField(blank=True)
    example_2 = models.TextField(blank=True)
    synonyms = models.TextField(blank=True)
    phonetic = models.CharField(max_length=100, blank=True)
    source_lang = models.CharField(max_length=10, default='en')
    target_lang = models.CharField(max_length=10, default='es')
    part_of_speech = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    # SM-2 logic
    ease_factor = models.FloatField(default=2.5)
    interval = models.IntegerField(default=1)
    repetitions = models.IntegerField(default=0)
    last_quality = models.IntegerField(default=0)
    last_review_at = models.DateTimeField(null=True, blank=True)
    next_review = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_review']

    def __str__(self):
        return f"{self.word} → {self.translation}"

    def is_due(self):
        return timezone.now() >= self.next_review

    def review(self, quality: int):
        self.last_review_at = timezone.now()
        
        if quality < 3:
            self.repetitions = 0
            self.interval = 1
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.ease_factor)

            self.repetitions += 1

        self.last_quality = quality
        self.ease_factor = max(1.3, self.ease_factor + 0.1 - (5 - quality) * 0.08) 
        self.next_review = timezone.now() + timezone.timedelta(days=self.interval)
        self.save()
