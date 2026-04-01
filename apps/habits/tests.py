from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Habit, HabitLog

User = get_user_model()


class HabitModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='habit_user1',
            email='hu1@example.com',
            password='Password123!'
        )
        self.client.login(username='habit_user1', password='Password123!')

        self.habit = Habit.objects.create(
            user=self.user,
            title='DSA Daily Practice',
            frequency='daily'
        )

