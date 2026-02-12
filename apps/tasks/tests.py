from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Task, Category, TaskHistory

User = get_user_model()


class TaskModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='Password123!'
        )
        self.other_user = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='Password123!'
        )
        self.client.login(username='user1', password='Password123!')

        self.category = Category.objects.create(
            user=self.user,
            name='Academics',
            color='#2563EB'
        )

        now = timezone.now()
        self.task = Task.objects.create(
            user=self.user,
            title='Solve LeetCode #15',
            category=self.category,
            priority='high',
            status='pending',
            due_at=now,
            estimated_duration=45
        )

    def test_my_day_view_renders(self):
        response = self.client.get(reverse('my_day'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/my_day.html')
        self.assertContains(response, 'Solve LeetCode #15')

    def test_quick_task_creation_in_my_day(self):
        response = self.client.post(reverse('my_day'), {
            'title': 'Read Clean Code Chapter 4',
            'priority': 'medium',
            'estimated_duration': 30
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(user=self.user, title='Read Clean Code Chapter 4').exists())
        # Check task history recorded
        task = Task.objects.get(user=self.user, title='Read Clean Code Chapter 4')
        self.assertTrue(TaskHistory.objects.filter(task=task, action='created').exists())

    def test_all_tasks_view_filters(self):
        # 1. Base view
        response = self.client.get(reverse('all_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/all_tasks.html')

        # 2. Search filter
        response = self.client.get(reverse('all_tasks') + '?q=LeetCode')
        self.assertContains(response, 'Solve LeetCode #15')

        # 3. Status filter
        response = self.client.get(reverse('all_tasks') + '?status=pending')
        self.assertContains(response, 'Solve LeetCode #15')

        response = self.client.get(reverse('all_tasks') + '?status=completed')
        self.assertNotContains(response, 'Solve LeetCode #15')

    def test_task_create_view(self):
        response = self.client.post(reverse('task_create'), {
            'title': 'Revise Operating Systems',
            'description': 'Virtual Memory and Paging',
            'category': self.category.id,
            'priority': 'high',
            'estimated_duration': 60,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(user=self.user, title='Revise Operating Systems').exists())

    def test_task_edit_view(self):
        response = self.client.post(reverse('task_edit', args=[self.task.id]), {
            'title': 'Solve LeetCode #15 - Updated',
            'priority': 'low',
            'estimated_duration': 20,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Solve LeetCode #15 - Updated')
        self.assertEqual(self.task.priority, 'low')

    def test_toggle_complete_task(self):
        # Toggle to completed
        response = self.client.post(reverse('task_toggle', args=[self.task.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')
        self.assertIsNotNone(self.task.completed_at)
        self.assertTrue(TaskHistory.objects.filter(task=self.task, action='completed').exists())

        # Toggle back to pending
        response = self.client.post(reverse('task_toggle', args=[self.task.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'pending')
        self.assertIsNone(self.task.completed_at)
        self.assertTrue(TaskHistory.objects.filter(task=self.task, action='marked_incomplete').exists())

    def test_toggle_complete_task_ajax(self):
        response = self.client.post(
            reverse('task_toggle', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'completed')
        self.assertTrue(data['is_completed'])

    def test_soft_delete_and_restore(self):
        # Soft delete
        response = self.client.post(reverse('task_delete', args=[self.task.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.deleted_at)
        self.assertFalse(Task.objects.active().filter(id=self.task.id).exists())
        self.assertTrue(Task.objects.deleted().filter(id=self.task.id).exists())

