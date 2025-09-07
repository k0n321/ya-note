import unittest

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note


class LogicTests(TestCase):
    """Логические проверки создания заметок (unittest-стиль)."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create(
            username='author', email='author@example.com'
        )
        cls.url = reverse('notes:add')
        cls.form_data = {
            'title': 'Test title',
            'text': 'Test text',
            'slug': 'test-title',
        }

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)
        # Проверяем редирект на страницу успеха.
        self.assertRedirects(response, reverse('notes:success'))
        # Проверяем, что заметка создана.
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        expected_redirect = f'{login_url}?next={self.url}'
        self.assertRedirects(response, expected_redirect)
        # В базе не должно появиться заметок.
        self.assertEqual(Note.objects.count(), 0)


if __name__ == '__main__':
    unittest.main()
