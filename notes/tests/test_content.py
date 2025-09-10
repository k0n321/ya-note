import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


class BaseTestCase(TestCase):
    """Базовый тест-кейс с общими фикстурами и URL."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create(
            username='user', email='user@example.com'
        )
        cls.author = User.objects.create(
            username='author', email='author@example.com'
        )
        cls.reader = User.objects.create(
            username='reader', email='reader@example.com'
        )
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.list_url = reverse('notes:list')
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')
        cls.home_url = reverse('notes:home')
        cls.signup_url = reverse('users:signup')
        cls.logout_url = reverse('users:logout')


class ContentTests(BaseTestCase):
    """Проверки содержимого контекста страниц приложения notes."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title='Author note', text='Some text', author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.readers_note = Note.objects.create(
            title='Readers note', text='Readers text', author=cls.reader
        )

    def test_author_sees_note_in_object_list(self):
        """
        Отдельная заметка автора передаётся на страницу списка заметок
        в списке object_list словаря context.
        """
        response = self.author_client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_other_user_does_not_see_note_in_object_list(self):
        """Другой пользователь не видит заметку автора в object_list."""
        response = self.reader_client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_user_notes_list_excludes_other_users_notes(self):
        """В список заметок одного
        пользователя не попадают заметки другого.
        """
        response = self.reader_client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertIn(self.readers_note, object_list)
        self.assertNotIn(self.note, object_list)
        self.assertEqual(list(object_list), [self.readers_note])

    def test_pages_contain_form_on_add_and_edit(self):
        """На страницах создания и редактирования передаётся форма NoteForm."""
        urls = (
            self.add_url,
            self.edit_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)


if __name__ == '__main__':
    unittest.main()
