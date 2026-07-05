from django.db import models
from django.conf import settings


class MLRecommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = [
        ('routine_task', 'Routine Task Suggestion'),
