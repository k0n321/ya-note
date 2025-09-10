import unittest
from http import HTTPStatus

from django.urls import reverse

from notes.models import Note
from notes.tests.test_content import BaseTestCase


class RoutesTests(BaseTestCase):
    """Тесты доступности маршрутов приложения notes."""

    def test_home_page_available_for_anonymous(self):
        """Главная и auth-страницы (логин, регистрация) доступны анониму."""
        urls = [self.home_url, self.login_url, self.signup_url]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title='Author note', text='Some text', author=cls.author
        )
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_authenticated_user_pages_available(self):
        """
        Аутентифицированному пользователю доступны:
        - список заметок `notes:list`
        - страница успеха `notes:success`
        - страница добавления `notes:add`
        """
        self.client.force_login(self.user)

        urls = [self.list_url, self.success_url, self.add_url]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_edit_delete_access_control(self):
        """
        Доступ к страницам заметки (detail, delete, edit) есть только у автора.
        Другому пользователю возвращается 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for url in (self.detail_url, self.delete_url, self.edit_url):
                with self.subTest(user=user, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Анонимный пользователь перенаправляется на страницу логина со всех
        защищённых страниц: список, успех, добавление, detail, edit, delete.
        """
        urls = (
            self.list_url,
            self.success_url,
            self.add_url,
            self.detail_url,
            self.edit_url,
            self.delete_url,
        )
        for url in urls:
            with self.subTest(url=url):
                redirect_url = f'{self.login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_logout_page_available_for_authenticated_user(self):
        """Страница выхода доступна авторизованному пользователю (POST)."""
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == '__main__':
    unittest.main()
