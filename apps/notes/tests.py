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

        self.note = Note.objects.create(
            user=self.user,
            title='Project Ideas',
            content='Build Habit Tracker with ML',
            is_pinned=False
        )

    def test_note_list_view(self):
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Project Ideas')

    def test_note_create(self):
        response = self.client.post(reverse('note_create'), {
            'title': 'DBMS Notes',
            'content': 'Third Normal Form requirements',
            'is_pinned': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Note.objects.filter(user=self.user, title='DBMS Notes', is_pinned=True).exists())

    def test_note_toggle_pin(self):
        self.assertFalse(self.note.is_pinned)
        response = self.client.post(reverse('note_toggle_pin', args=[self.note.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_pinned)
