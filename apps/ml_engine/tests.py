from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.tasks.models import Task, TaskHistory
from .models import MLRecommendation
from .services import RecommendationEngine

User = get_user_model()


class MLEngineModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ml_user',
            email='mlu@example.com',
            password='Password123!'
        )
        self.client.login(username='ml_user', password='Password123!')

        self.task = Task.objects.create(
            user=self.user,
            title='Pending Task for Review',
            status='pending',
            due_at=timezone.now()
        )

    def test_daily_summary_calculation(self):
        summary = RecommendationEngine.calculate_daily_summary(self.user)
        self.assertEqual(summary.total_tasks, 1)
        self.assertEqual(summary.pending_tasks, 1)
        self.assertEqual(summary.completed_tasks, 0)
        self.assertEqual(summary.completion_percentage, 0.0)

    def test_end_of_day_review_view(self):
        response = self.client.get(reverse('end_of_day_review'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pending Task for Review')
        self.assertContains(response, 'End-of-Day Review')

    def test_apply_rollover_to_tomorrow(self):
        response = self.client.post(reverse('apply_rollover'), {
            'action': 'rollover_tomorrow',
            'task_ids': [str(self.task.id)],
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertGreater(self.task.due_at, timezone.now())
        self.assertTrue(TaskHistory.objects.filter(task=self.task, action='rolled_over_to_tomorrow').exists())
