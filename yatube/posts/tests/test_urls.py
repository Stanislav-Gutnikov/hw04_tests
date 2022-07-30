from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from http import HTTPStatus

from posts.models import Post, Group


User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user,
        )
        cls.post_id = cls.post.id
        cls.urls = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/posts/{cls.post_id}/': HTTPStatus.OK,
            f'/profile/{cls.user.username}/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{cls.post_id}/edit/': HTTPStatus.OK
        }

    def setUp(self) -> None:
        #  Создание неавторизованного пользователя
        self.user = User.objects.create_user(username='NoName')
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client(self):
        '''Какие страницы доступны неавторизованному пользователю '''
        urls = self.urls
        self.urls['/create/'] = HTTPStatus.FOUND
        self.urls[f'/posts/{self.post_id}/edit/'] = HTTPStatus.FOUND
        for url, response_code in urls.items():
            with self.subTest(url=url):
                status_code = self.client.get(url).status_code
                self.assertEqual(response_code, status_code)

    def test_authorized_client(self):
        '''Какие страницы доступны авторизованному пользователю '''
        #  Если пользователь авторизован,
        #  и является автором поста - должны быть доступны все страницы
        if self.post.author == self.user.username:
            urls = self.urls
            for url, response_code in urls.items():
                with self.subTest(url=url):
                    status_code = self.authorized_client.get(url).status_code
                    self.assertEqual(response_code, status_code)
        #  Если пользователь не является автором поста
        #  должна быть недоступна страница редактирования поста
        else:
            self.urls[f'/posts/{self.post_id}/edit/'] = HTTPStatus.FOUND
            urls = self.urls
            for url, response_code in urls.items():
                with self.subTest(url=url):
                    status_code = self.authorized_client.get(url).status_code
                    self.assertEqual(response_code, status_code)

    def test_guest_redirect_login(self):
        '''Направит ли неавторизованного пользователя
           на страницу авторизации при попытке перейти на
           '/create/', '/posts/<post_id>/edit/' '''
        urls = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post_id}/edit/': '/auth/login/?next=/posts/1/edit/'
        }
        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, template)
