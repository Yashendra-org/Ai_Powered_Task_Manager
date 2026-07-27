# Stage 2/5: Progressive implementation
from django.db import models
from django.conf import settings
from django.utils import timezone


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekdays', 'Weekdays (Mon-Fri)'),
        ('custom', 'Custom Days'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='habits')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    scheduled_days = models.JSONField(default=list, blank=True, help_text="List of day indices [0=Mon, 6=Sun]")
    target_time = models.TimeField(null=True, blank=True)
    monthly_goal = models.PositiveIntegerField(default=20, help_text="Target completions per month/period")
    color = models.CharField(max_length=20, default="#10B981", help_text="Hex color token")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'habits_habit'
        ordering = ['title']

    def __str__(self):
        return self.title

