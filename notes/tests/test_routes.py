import unittest
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note


class RoutesTests(TestCase):
    """Тесты доступности маршрутов приложения notes."""

    def test_home_page_available_for_anonymous(self):
        """Главная и auth-страницы (логин, регистрация) доступны анониму."""
        urls = [
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create(
            username='tester', email='tester@example.com'
        )
        cls.author = User.objects.create(
            username='author', email='author@example.com'
        )
        cls.reader = User.objects.create(
            username='reader', email='reader@example.com'
        )
        cls.note = Note.objects.create(
            title='Author note', text='Some text', author=cls.author
        )

    def test_authenticated_user_pages_available(self):
        """
        Аутентифицированному пользователю доступны:
        - список заметок `notes:list`
        - страница успеха `notes:success`
        - страница добавления `notes:add`
        """
        self.client.force_login(self.user)

        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

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
            for name in ('notes:detail', 'notes:delete', 'notes:edit'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Анонимный пользователь перенаправляется на страницу логина со всех
        защищённых страниц: список, успех, добавление, detail, edit, delete.
        """
        login_url = reverse('users:login')

        names_with_args = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in names_with_args:
            with self.subTest(name=name):
                url = reverse(name, args=args) if args else reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_logout_page_available_for_authenticated_user(self):
        """Страница выхода доступна авторизованному пользователю (POST)."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


if __name__ == '__main__':
    unittest.main()
