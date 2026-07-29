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

    def current_streak(self):
        """Calculates the consecutive streak ending today or yesterday."""
        logs = set(self.logs.filter(status='completed').values_list('date', flat=True))
        if not logs:
            return 0
        streak = 0
        today = timezone.localdate()
        current = today
        # If today is not logged, start checking from yesterday
        if current not in logs:
            current -= timezone.timedelta(days=1)
        while current in logs:
            streak += 1
            current -= timezone.timedelta(days=1)
        return streak


class HabitLog(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    ]

    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='completed')
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'habits_habit_log'
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.title} on {self.date} ({self.status})"
