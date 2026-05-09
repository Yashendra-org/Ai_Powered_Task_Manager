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

    def test_habit_list_view(self):
        response = self.client.get(reverse('habit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DSA Daily Practice')

    def test_habit_toggle_log(self):
        today = timezone.localdate()
        today_str = today.strftime('%Y-%m-%d')

        # Check in for today
        response = self.client.post(
            reverse('habit_toggle_log', args=[self.habit.id]),
            {'date': today_str},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(HabitLog.objects.filter(habit=self.habit, date=today, status='completed').exists())
        self.assertEqual(self.habit.current_streak(), 1)

        # Uncheck
        response = self.client.post(
            reverse('habit_toggle_log', args=[self.habit.id]),
            {'date': today_str},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
