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
