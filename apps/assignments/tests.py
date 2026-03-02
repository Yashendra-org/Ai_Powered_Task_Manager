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
