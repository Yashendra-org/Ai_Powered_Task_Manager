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
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_habit_user_active'),
        ]

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

    @staticmethod
    def compute_streaks_for_habits(habits, today=None, lookback_days=365):
        """
        Batched O(1)-query streak and today-completion calculation for a list of habits.
        Eliminates N+1 HabitLog queries on Dashboard and REST API list endpoints.
        Returns tuple: (streaks_by_habit_id, completed_today_ids)
        """
        habit_list = list(habits)
        if not habit_list:
            return {}, set()

        today = today or timezone.localdate()
        cutoff = today - timezone.timedelta(days=lookback_days)
        rows = HabitLog.objects.filter(
            habit_id__in=[h.id for h in habit_list],
            status='completed',
            date__gte=cutoff,
        ).values_list('habit_id', 'date')

        dates_by_habit = {}
        completed_today_ids = set()
        for hid, log_date in rows:
            dates_by_habit.setdefault(hid, set()).add(log_date)
            if log_date == today:
                completed_today_ids.add(hid)

        streaks = {}
        for h in habit_list:
            logs = dates_by_habit.get(h.id)
            if not logs:
                streaks[h.id] = 0
                continue
            streak = 0
            current = today if today in logs else (today - timezone.timedelta(days=1))
            while current in logs:
                streak += 1
                current -= timezone.timedelta(days=1)
            streaks[h.id] = streak

        return streaks, completed_today_ids


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
        indexes = [
            models.Index(fields=['habit', 'status', '-date'], name='idx_hlog_habit_stat_date'),
        ]

    def __str__(self):
        return f"{self.habit.title} on {self.date} ({self.status})"
