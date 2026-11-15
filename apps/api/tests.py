# Stage 2/5: Implementation refinement
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

