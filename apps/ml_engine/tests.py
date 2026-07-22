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

    def test_recommendation_feedback_accept(self):
        rec = MLRecommendation.objects.create(
            user=self.user,
            recommendation_type='routine_task',
            title="Scheduled Routine: 'DSA Practice'",
            explanation='You do this often',
            status='pending'
        )
        response = self.client.post(
            reverse('recommendation_feedback', args=[rec.id, 'accept']),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'accepted')
        # Routine task should have been created
        self.assertTrue(Task.objects.filter(user=self.user, title='DSA Practice').exists())

    def test_recommendation_feedback_reject(self):
        rec = MLRecommendation.objects.create(
            user=self.user,
            recommendation_type='optimal_time',
            title='Study Earlier',
            explanation='Morning focus is higher',
            status='pending'
        )
        response = self.client.post(
            reverse('recommendation_feedback', args=[rec.id, 'reject']),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'rejected')
