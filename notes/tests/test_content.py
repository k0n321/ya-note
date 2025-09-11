import unittest

from notes.forms import NoteForm
from notes.tests.base import BaseTestCase


class ContentTests(BaseTestCase):
    """Проверки содержимого контекста страниц приложения notes."""

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
