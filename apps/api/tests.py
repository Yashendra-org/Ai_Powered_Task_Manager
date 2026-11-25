from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()


class RestApiModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apitest', password='password123')
        self.client.login(username='apitest', password='password123')
        self.task = Task.objects.create(
            user=self.user,
            title='Test API Task',
            priority='high',
            status='pending'
        )

    def test_api_root_endpoint(self):
        response = self.client.get(reverse('api_root'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))
        self.assertEqual(response.json().get('name'), 'My Habit Tracker REST API')

    def test_tasks_api_listing_and_creation(self):
        response = self.client.get(reverse('api_tasks_list_create'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['count'], 1)

        create_response = self.client.post(
            reverse('api_tasks_list_create'),
            {'title': 'New via API', 'priority': 'medium'},
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()['data']['title'], 'New via API')

    def test_task_toggle_api(self):
        url = reverse('api_tasks_toggle', kwargs={'pk': self.task.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], 'completed')

    def test_negative_duration_rejected_by_api(self):
        """Vibe Coding Audit (Item 05 Negative Quantity Exploit)"""
        url = reverse('api_tasks_list_create')
        res = self.client.post(
            url,
            {'title': 'Exploit Task', 'estimated_duration': -50},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['error']['code'], 'VALIDATION_FAILED')

    def test_unauthenticated_access_blocked(self):
        """Vibe Coding Audit (Item 01 Broken Access Control)"""
        self.client.logout()
        res = self.client.get(reverse('api_tasks_list_create'))
        self.assertIn(res.status_code, (401, 403))

    def test_task_toggle_cross_user_idor_blocked(self):
        """Vibe Coding Audit (Item 02 IDOR / BOLA Prevention)"""
        User.objects.create_user(username='attacker', email='attacker@example.com', password='password123')
        self.client.login(username='attacker', password='password123')
        url = reverse('api_tasks_toggle', kwargs={'pk': self.task.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 404)


