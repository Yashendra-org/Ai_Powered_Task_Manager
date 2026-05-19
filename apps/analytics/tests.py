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
