from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Task, Category, TaskHistory

User = get_user_model()


class TaskModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='Password123!'
        )
        self.other_user = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='Password123!'
        )
        self.client.login(username='user1', password='Password123!')

        self.category = Category.objects.create(
            user=self.user,
            name='Academics',
            color='#2563EB'
        )

        now = timezone.now()
        self.task = Task.objects.create(
            user=self.user,
