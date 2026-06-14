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
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
