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
    title = models.CharField(max_length=255)
    explanation = models.TextField()
    suggested_date = models.DateField(null=True, blank=True)
    suggested_time = models.TimeField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True, help_text="Calibrated confidence [0.0 - 1.0]")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ml_engine_recommendation'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.recommendation_type}] {self.title} ({self.status})"
