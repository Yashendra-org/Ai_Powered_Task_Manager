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

    def test_global_search_api_omnibar(self):
        """Pillar 5, #17: Global Omnibar Search Endpoint Tests"""
        # Create user notes and habits
        from apps.habits.models import Habit
        from apps.notes.models import Note
        Habit.objects.create(user=self.user, title='Morning Meditation Routine', frequency='daily')
        Note.objects.create(user=self.user, title='Physics Lecture Formulae', content='Thermodynamics laws')

        # Create another user's private task
        other_user = User.objects.create_user(username='other_tenant', email='other_tenant@example.com', password='password123')
        Task.objects.create(user=other_user, title='Confidential Private Other Task')

        # Search for 'test'
        res = self.client.get(reverse('api_search') + '?q=test')
        self.assertEqual(res.status_code, 200)
        data = res.json()['data']
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Test API Task')

        # Search for 'formulae'
        res_note = self.client.get(reverse('api_search') + '?q=formulae')
        self.assertEqual(res_note.status_code, 200)
        self.assertEqual(len(res_note.json()['data']['notes']), 1)
        self.assertEqual(res_note.json()['data']['notes'][0]['title'], 'Physics Lecture Formulae')

        # Search for 'meditation'
        res_habit = self.client.get(reverse('api_search') + '?q=meditation')
        self.assertEqual(res_habit.status_code, 200)
        self.assertEqual(len(res_habit.json()['data']['habits']), 1)
        self.assertEqual(res_habit.json()['data']['habits'][0]['title'], 'Morning Meditation Routine')

        # Ensure cross-tenant data leakage is prevented
        res_leak = self.client.get(reverse('api_search') + '?q=confidential')
        self.assertEqual(res_leak.status_code, 200)
        self.assertEqual(len(res_leak.json()['data']['tasks']), 0)



