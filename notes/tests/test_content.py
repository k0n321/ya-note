import unittest

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm


class ContentTests(TestCase):
    """Проверки содержимого контекста страниц приложения notes."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.author = User.objects.create(
            username='author', email='author@example.com'
        )
        cls.reader = User.objects.create(
            username='reader', email='reader@example.com'
        )
        cls.note = Note.objects.create(
            title='Author note', text='Some text', author=cls.author
        )

    def test_author_sees_note_in_object_list(self):
        """
        Отдельная заметка автора передаётся на страницу списка заметок
        в списке object_list словаря context.
        """
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_other_user_does_not_see_note_in_object_list(self):
        """Другой пользователь не видит заметку автора в object_list."""
        self.client.force_login(self.reader)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_user_notes_list_excludes_other_users_notes(self):
        """В список заметок одного
        пользователя не попадают заметки другого.
        """
        # Создаём заметку для другого пользователя (reader).
        readers_note = Note.objects.create(
            title='Readers note', text='Readers text', author=self.reader
        )
        # Логинимся под reader и проверяем, что видна только его заметка.
        self.client.force_login(self.reader)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertIn(readers_note, object_list)
        self.assertNotIn(self.note, object_list)
        self.assertEqual(list(object_list), [readers_note])

    def test_pages_contain_form_on_add_and_edit(self):
        """На страницах создания и редактирования передаётся форма NoteForm."""
        self.client.force_login(self.author)
        names_with_args = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in names_with_args:
            with self.subTest(name=name):
                url = reverse(name, args=args) if args else reverse(name)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)


if __name__ == '__main__':
    unittest.main()
