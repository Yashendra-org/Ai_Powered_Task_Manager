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
