from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Assignment, Subject, Teacher

User = get_user_model()


class AssignmentModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='student1',
            email='student1@college.edu',
            password='Password123!'
        )
        self.other_user = User.objects.create_user(
            username='student2',
            email='student2@college.edu',
            password='Password123!'
        )
        self.client.login(username='student1', password='Password123!')

        self.subject = Subject.objects.create(
            user=self.user,
            name='Database Systems',
            code='CS302'
        )

        now = timezone.now()
        self.assignment = Assignment.objects.create(
            user=self.user,
            subject=self.subject,
            title='Homework 1: SQL Joins',
            due_at=now + timezone.timedelta(days=2),
            priority='high',
            status='not_started'
        )

    def test_assignment_list_view(self):
        response = self.client.get(reverse('assignment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Homework 1: SQL Joins')
        self.assertContains(response, 'CS302')

    def test_deadline_categorization(self):
        now = timezone.now()
        # Due in 3 days -> due_soon
        self.assignment.due_at = now + timezone.timedelta(days=3)
        self.assertEqual(self.assignment.deadline_category, 'due_soon')

        # Due later today (in 4 hours) -> due_today
        self.assignment.due_at = now + timezone.timedelta(hours=4)
        self.assertEqual(self.assignment.deadline_category, 'due_today')

        # Overdue (2 days ago)
        self.assignment.due_at = now - timezone.timedelta(days=2)
        self.assertEqual(self.assignment.deadline_category, 'overdue')

    def test_submit_toggle(self):
        response = self.client.post(reverse('assignment_submit_toggle', args=[self.assignment.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.status, 'submitted')
        self.assertIsNotNone(self.assignment.submitted_at)

        # Toggle back
        response = self.client.post(reverse('assignment_submit_toggle', args=[self.assignment.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.status, 'in_progress')
        self.assertIsNone(self.assignment.submitted_at)

    def test_user_data_isolation(self):
        self.client.login(username='student2', password='Password123!')
        res = self.client.get(reverse('assignment_list'))
        self.assertNotContains(res, 'Homework 1: SQL Joins')

        # Attempt to edit or delete User 1's assignment
        edit_res = self.client.get(reverse('assignment_edit', args=[self.assignment.id]))
        self.assertEqual(edit_res.status_code, 404)

        del_res = self.client.post(reverse('assignment_delete', args=[self.assignment.id]))
        self.assertEqual(del_res.status_code, 404)
