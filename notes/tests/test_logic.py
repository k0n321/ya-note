import unittest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.test_content import BaseTestCase


class LogicTests(BaseTestCase):
    """Логические проверки создания заметок (unittest-стиль)."""

    def setUp(self):
        Note.objects.all().delete()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('notes:add')
        cls.form_data = {
            'title': 'Test title',
            'text': 'Test text',
            'slug': 'test-title',
        }

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        start_count = Note.objects.count()
        response = self.user_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), start_count + 1)
        note = Note.objects.get(slug=self.form_data['slug'])
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        start_count = Note.objects.count()
        response = self.client.post(self.url, data=self.form_data)
        expected_redirect = f'{self.login_url}?next={self.url}'
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Note.objects.count(), start_count)

    def test_cannot_create_two_notes_with_same_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        start_count = Note.objects.count()
        first_response = self.user_client.post(self.url, data=self.form_data)
        self.assertRedirects(first_response, self.success_url)
        self.assertEqual(Note.objects.count(), start_count + 1)
        dup_data = {
            'title': 'Another title',
            'text': 'Another text',
            'slug': self.form_data['slug'],
        }
        response = self.user_client.post(self.url, data=dup_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFormError(
            response.context['form'],
            'slug',
            dup_data['slug'] + WARNING,
        )
        self.assertEqual(Note.objects.count(), start_count + 1)

    def test_author_can_edit_and_delete_own_note(self):
        """Пользователь может редактировать и удалять свою заметку."""
        start_count = Note.objects.count()
        note = Note.objects.create(
            title='Original', text='Text', author=self.user
        )
        edit_url = reverse('notes:edit', args=(note.slug,))
        updated = {'title': 'Updated', 'text': 'New text', 'slug': 'updated'}
        response = self.user_client.post(edit_url, data=updated)
        self.assertRedirects(response, self.success_url)
        updated_note = Note.objects.get(id=note.id)
        self.assertEqual(updated_note.title, updated['title'])
        self.assertEqual(updated_note.text, updated['text'])
        self.assertEqual(updated_note.slug, updated['slug'])
        self.assertEqual(updated_note.author, self.user)

        delete_url = reverse('notes:delete', args=(updated_note.slug,))
        response = self.user_client.post(delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), start_count)

    def test_user_cannot_edit_or_delete_others_note(self):
        """Пользователь не может редактировать или удалять чужие заметки."""
        start_count = Note.objects.count()
        User = get_user_model()
        other_user = User.objects.create(
            username='stranger', email='stranger@example.com'
        )
        note = Note.objects.create(
            title='Author title', text='Author text', author=self.user
        )
        self.client.force_login(other_user)

        with self.subTest(action='edit as stranger'):
            edit_url = reverse('notes:edit', args=(note.slug,))
            updated = {'title': 'Hacker', 'text': 'Hack', 'slug': 'hacked'}
            response = self.client.post(edit_url, data=updated)
            self.assertEqual(
                response.status_code, HTTPStatus.NOT_FOUND,
                msg='Stranger should not edit others note',
            )
            unchanged = Note.objects.get(id=note.id)
            self.assertEqual(unchanged.title, note.title)
            self.assertEqual(unchanged.text, note.text)
            self.assertEqual(unchanged.slug, note.slug)
            self.assertEqual(unchanged.author, note.author)

        with self.subTest(action='delete as stranger'):
            delete_url = reverse('notes:delete', args=(note.slug,))
            response = self.client.post(delete_url)
            self.assertEqual(
                response.status_code, HTTPStatus.NOT_FOUND,
                msg='Stranger should not delete others note',
            )
            self.assertEqual(Note.objects.count(), start_count + 1)

    def test_empty_slug_is_generated_automatically(self):
        """
        Если slug не передан, он формируется автоматически
        через slugify(title).
        """
        start_count = Note.objects.count()
        data = self.form_data.copy()
        data.pop('slug')
        expected_slug = slugify(data['title'])

        with self.subTest(step='auto slug generation'):
            response = self.user_client.post(self.url, data=data)
            self.assertRedirects(response, self.success_url)
            self.assertEqual(Note.objects.count(), start_count + 1)
            note = Note.objects.get(slug=expected_slug)
            self.assertEqual(note.slug, expected_slug)

        with self.subTest(step='duplicate slug error'):
            dup_data = {
                'title': 'Another title',
                'text': 'Another text',
                'slug': expected_slug,
            }
            response = self.user_client.post(self.url, data=dup_data)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(Note.objects.count(), start_count + 1)
            self.assertFormError(
                response.context['form'],
                'slug',
                expected_slug + WARNING,
            )
            self.assertEqual(
                Note.objects.get(slug=expected_slug).author,
                self.user,
            )


if __name__ == '__main__':
    unittest.main()
