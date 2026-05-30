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
