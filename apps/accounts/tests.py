from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationAndDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')
        self.settings_url = reverse('settings')

    def test_registration_view_renders(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_login_view_renders(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_user_registration_and_login_flow(self):
        post_data = {
            'username': 'student_yashendra',
            'email': 'student@example.com',
            'timezone': 'Asia/Kolkata',
            'password1': 'StrongP@ssw0rd123!',
            'password2': 'StrongP@ssw0rd123!',
        }
        response = self.client.post(self.register_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'student_yashendra')
        self.assertEqual(response.context['user'].timezone, 'Asia/Kolkata')
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.dashboard_url)
