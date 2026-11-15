# Stage 3/5: Implementation refinement
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()


class RestApiModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apitest', password='password123')
        self.client.login(username='apitest', password='password123')
        self.task = Task.objects.create(
            user=self.user,
            title='Test API Task',
            priority='high',
            status='pending'
        )

    def test_api_root_endpoint(self):
        response = self.client.get(reverse('api_root'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))
        self.assertEqual(response.json().get('name'), 'My Habit Tracker REST API')

    def test_tasks_api_listing_and_creation(self):
        response = self.client.get(reverse('api_tasks_list_create'))
