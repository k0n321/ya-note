import unittest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
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

    def test_cannot_create_two_notes_with_same_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        self.client.force_login(self.user)
        # Создаём первую заметку.
        first_response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(first_response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_and_delete_own_note(self):
        """Пользователь может редактировать и удалять свою заметку."""
        # Готовим автора и его заметку.
        note = Note.objects.create(
            title='Original', text='Text', author=self.user
        )
        self.client.force_login(self.user)

        # Редактирование своей заметки.
        edit_url = reverse('notes:edit', args=(note.slug,))
        updated = {'title': 'Updated', 'text': 'New text', 'slug': 'updated'}
        response = self.client.post(edit_url, data=updated)
        self.assertRedirects(response, reverse('notes:success'))
        note.refresh_from_db()
        self.assertEqual(note.title, updated['title'])
        self.assertEqual(note.text, updated['text'])
        self.assertEqual(note.slug, updated['slug'])

        # Удаление своей заметки.
        delete_url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cannot_edit_or_delete_others_note(self):
        """Пользователь не может редактировать или удалять чужие заметки."""
        User = get_user_model()
        other_user = User.objects.create(
            username='stranger', email='stranger@example.com'
        )
        # Заметка принадлежит self.user (автор).
        note = Note.objects.create(
            title='Author title', text='Author text', author=self.user
        )
        # Логинимся под другим пользователем.
        self.client.force_login(other_user)

        # Попытка редактирования чужой заметки.
        edit_url = reverse('notes:edit', args=(note.slug,))
        updated = {'title': 'Hacker', 'text': 'Hack', 'slug': 'hacked'}
        response = self.client.post(edit_url, data=updated)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note.refresh_from_db()
        self.assertEqual(note.title, 'Author title')
        self.assertEqual(note.text, 'Author text')
        self.assertNotEqual(note.slug, 'hacked')

        # Попытка удаления чужой заметки.
        delete_url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_is_generated_automatically(self):
        """
        Если slug не передан, он формируется автоматически
        через slugify(title).
        """
        self.client.force_login(self.user)
        data = self.form_data.copy()
        # Имитируем отсутствие slug в отправленных данных.
        data.pop('slug')
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        expected_slug = slugify(data['title'])
        self.assertEqual(note.slug, expected_slug)
        # Пытаемся создать вторую заметку с тем же slug.
        dup_data = {
            'title': 'Another title',
            'text': 'Another text',
            'slug': self.form_data['slug'],
        }
        response = self.client.post(self.url, data=dup_data)
        # Должна вернуться та же страница формы c ошибкой (без редиректа).
        self.assertEqual(response.status_code, 200)
        # Проверяем ошибку формы на поле slug
        # и что количество записей не изменилось.
        self.assertFormError(
            response.context['form'],
            'slug',
            dup_data['slug'] + WARNING,
        )
        self.assertEqual(Note.objects.count(), 1)


if __name__ == '__main__':
    unittest.main()
