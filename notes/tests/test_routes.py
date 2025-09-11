import unittest
from http import HTTPStatus

from notes.tests.base import BaseTestCase


class RoutesTests(BaseTestCase):
    """Тесты доступности маршрутов приложения notes."""

    def test_home_page_available_for_anonymous(self):
        """Главная и auth-страницы (логин, регистрация) доступны анониму."""
        urls = [self.home_url, self.login_url, self.signup_url]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authenticated_user_pages_available(self):
        """
        Аутентифицированному пользователю доступны:
        - список заметок `notes:list`
        - страница успеха `notes:success`
        - страница добавления `notes:add`
        """
        urls = [self.list_url, self.success_url, self.add_url]
        for url in urls:
            with self.subTest(url=url):
                response = self.user_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_edit_delete_access_control(self):
        """
        Доступ к страницам заметки (detail, delete, edit) есть только у автора.
        Другому пользователю возвращается 404.
        """
        clients_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for client, status in clients_statuses:
            for url in (self.detail_url, self.delete_url, self.edit_url):
                with self.subTest(url=url):
                    response = client.get(url)
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
        response = self.user_client.post(self.logout_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == '__main__':
    unittest.main()
