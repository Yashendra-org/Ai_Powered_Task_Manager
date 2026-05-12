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
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upcoming Assignment')

    def test_mark_as_read(self):
        self.assertFalse(self.notif.is_read)
        response = self.client.post(reverse('notification_mark_read', args=[self.notif.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(user=self.user, title='N2', message='M2', is_read=False)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 2)

        response = self.client.post(reverse('notification_mark_all_read'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)
