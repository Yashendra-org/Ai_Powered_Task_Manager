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
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_daily_summary'
        verbose_name_plural = 'Daily summaries'
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.completion_percentage}%"
