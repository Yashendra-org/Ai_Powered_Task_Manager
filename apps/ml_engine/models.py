from django.db import models
from django.conf import settings


class MLRecommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = [
        ('routine_task', 'Routine Task Suggestion'),
        ('optimal_time', 'Optimal Time Recommendation'),
        ('reschedule', 'Smart Rescheduling'),
        ('completion_risk', 'Completion Risk Warning'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
