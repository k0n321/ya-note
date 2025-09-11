from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
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
        cls.note = Note.objects.create(
            title='Author note', text='Some text', author=cls.author
        )
        cls.readers_note = Note.objects.create(
            title='Readers note', text='Readers text', author=cls.reader
        )
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
