from django.db import models
from django.conf import settings
from django.utils import timezone


class DailySummary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField(default=timezone.localdate)
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    pending_tasks = models.PositiveIntegerField(default=0)
    overdue_tasks = models.PositiveIntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
