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
            status__in=['pending', 'in_progress']
        )
        if overdue_tasks.exists():
            count = overdue_tasks.count()
            rec, _ = MLRecommendation.objects.get_or_create(
                user=user,
                recommendation_type='reschedule',
                title=f"Rollover {count} Overdue Task{'s' if count > 1 else ''}",
                defaults={
                    'explanation': f"You have {count} unfinished task(s) past deadline. Consider moving them to tomorrow or rescheduling during your End-of-Day Review.",
                    'suggested_date': today + timedelta(days=1),
                    'confidence_score': 0.95,
                    'status': 'pending'
                }
            )
            recommendations.append(rec)

        # 2. Routine Detection (Frequency Analysis)
        # Find tasks with identical titles completed 3+ times in the last 14 days
        past_two_weeks = now - timedelta(days=14)
        completed_hist = TaskHistory.objects.filter(
            task__user=user,
            action='completed',
            recorded_at__gte=past_two_weeks
