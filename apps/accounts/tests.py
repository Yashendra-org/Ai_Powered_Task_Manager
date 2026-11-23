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
        self.delete_account_url = reverse('delete_account')

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
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_settings_view_updates_preferences(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!',
            timezone='Asia/Kolkata',
            daily_review_time='21:30'
        )
        self.client.login(username='testuser', password='TestPassword123!')
        
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, 200)

        # Update settings
        update_data = {
            'email': 'updated@example.com',
            'timezone': 'UTC',
            'daily_review_time': '22:00:00',
        }
        post_response = self.client.post(self.settings_url, update_data, follow=True)
        self.assertEqual(post_response.status_code, 200)
        
        user.refresh_from_db()
        self.assertEqual(user.email, 'updated@example.com')
        self.assertEqual(user.timezone, 'UTC')
        self.assertEqual(str(user.daily_review_time), '22:00:00')
