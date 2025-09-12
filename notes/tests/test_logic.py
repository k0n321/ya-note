import unittest
from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.base import BaseTestCase


class LogicTests(BaseTestCase):
    """Логические проверки создания заметок (unittest-стиль)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.form_data = {
            'title': 'Test title',
            'text': 'Test text',
            'slug': 'test-title',
        }

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        Note.objects.all().delete()
        response = self.user_client.post(self.add_url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        self.assertRedirects(response, self.success_url)
        note = Note.objects.get()
        self.assertIsNotNone(note)
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        start_count = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        expected_redirect = f'{self.login_url}?next={self.add_url}'
        self.assertEqual(Note.objects.count(), start_count)
        self.assertRedirects(response, expected_redirect)

    def test_cannot_create_two_notes_with_same_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        start_count = Note.objects.count()
        dup_data = {
            'title': 'Another title',
            'text': 'Another text',
            'slug': self.note.slug,
        }
        response = self.user_client.post(self.add_url, data=dup_data)
        self.assertEqual(Note.objects.count(), start_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response.context['form'],
            'slug',
            dup_data['slug'] + WARNING,
        )

    def test_author_can_edit_own_note(self):
        """Пользователь-автор может редактировать свою заметку."""
        start_count = Note.objects.count()
        updated = {'title': 'Updated', 'text': 'New text', 'slug': 'updated'}
        response = self.author_client.post(self.edit_url, data=updated)
        self.assertEqual(Note.objects.count(), start_count)
        self.assertRedirects(response, self.success_url)
        updated_note = Note.objects.get(id=self.note.id)
        self.assertEqual(updated_note.title, updated['title'])
        self.assertEqual(updated_note.text, updated['text'])
        self.assertEqual(updated_note.slug, updated['slug'])
        self.assertEqual(updated_note.author, self.note.author)

    def test_author_can_delete_own_note(self):
        """Пользователь-автор может удалить свою заметку."""
        start_count = Note.objects.count()
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), start_count - 1)

    def test_user_cannot_edit_or_delete_others_note(self):
        """Пользователь не может редактировать или удалять чужие заметки."""
        start_count = Note.objects.count()
        self.client.force_login(self.reader)

        with self.subTest(action='edit as stranger'):
            updated = {'title': 'Hacker', 'text': 'Hack', 'slug': 'hacked'}
            response = self.client.post(self.edit_url, data=updated)
            self.assertEqual(
                response.status_code, HTTPStatus.NOT_FOUND,
                msg='Stranger should not edit others note',
            )
            unchanged = Note.objects.get(id=self.note.id)
            self.assertEqual(unchanged.title, self.note.title)
            self.assertEqual(unchanged.text, self.note.text)
            self.assertEqual(unchanged.slug, self.note.slug)
            self.assertEqual(unchanged.author, self.note.author)

        with self.subTest(action='delete as stranger'):
            response = self.client.post(self.delete_url)
            self.assertEqual(Note.objects.count(), start_count)
            self.assertEqual(
                response.status_code, HTTPStatus.NOT_FOUND,
                msg='Stranger should not delete others note',
            )

    def test_empty_slug_is_generated_automatically(self):
        """
        Если slug не передан, он формируется автоматически
        через slugify(title).
        """
        Note.objects.all().delete()
        data = self.form_data.copy()
        data.pop('slug')
        expected_slug = slugify(data['title'])

        with self.subTest(step='auto slug generation'):
            response = self.user_client.post(self.add_url, data=data)
            self.assertEqual(Note.objects.count(), 1)
            self.assertRedirects(response, self.success_url)
            note = Note.objects.get()
            self.assertIsNotNone(note)
            self.assertEqual(note.slug, expected_slug)

        with self.subTest(step='duplicate slug error'):
            dup_data = {
                'title': 'Another title',
                'text': 'Another text',
                'slug': expected_slug,
            }
            response = self.user_client.post(self.add_url, data=dup_data)
            self.assertEqual(Note.objects.count(), 1)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFormError(
                response.context['form'],
                'slug',
                expected_slug + WARNING,
            )


if __name__ == '__main__':
    unittest.main()
