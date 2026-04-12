from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Note

User = get_user_model()


class NoteModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='note_user',
            email='nu@example.com',
            password='Password123!'
        )
        self.client.login(username='note_user', password='Password123!')

