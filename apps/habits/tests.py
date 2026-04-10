from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Habit, HabitLog

User = get_user_model()


class HabitModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
