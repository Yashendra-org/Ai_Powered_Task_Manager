from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.tasks.models import Task, Category

User = get_user_model()


class AnalyticsAndCalendarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='analytics_user',
            email='au@example.com',
            password='Password123!'
        )
        self.client.login(username='analytics_user', password='Password123!')

        cat = Category.objects.create(user=self.user, name='Study')
        Task.objects.create(
            user=self.user,
            title='Task 1',
            category=cat,
            status='completed',
            due_at=timezone.now()
        )

    def test_analytics_dashboard_view(self):
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Productivity Analytics')
        self.assertContains(response, 'velocityChart')

    def test_calendar_view(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task 1')
