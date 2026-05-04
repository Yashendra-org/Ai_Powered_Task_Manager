from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


class ReminderModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='rem_user',
            email='rem@example.com',
            password='Password123!'
        )
        self.client.login(username='rem_user', password='Password123!')

        self.notif = Notification.objects.create(
            user=self.user,
            title='Upcoming Assignment',
            message='DBMS Assignment 3 is due soon.',
            notification_type='deadline',
            is_read=False
        )

    def test_notification_list_view(self):
