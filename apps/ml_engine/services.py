from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task, TaskHistory
from apps.analytics.models import DailySummary
from .models import MLRecommendation


class RecommendationEngine:
    @staticmethod
    def generate_recommendations(user):
        """
        Hybrid Intelligence Engine:
        1. Rule-based deadline urgency & overdue detection
        2. Frequency-based recurring routine suggestions
        3. Completion probability estimation
        """
        now = timezone.now()
        today = timezone.localdate()
        recommendations = []

        # 1. Overdue Rollover Suggestion (Rule-Based)
        overdue_tasks = Task.objects.active().filter(
            user=user,
            due_at__lt=now,
