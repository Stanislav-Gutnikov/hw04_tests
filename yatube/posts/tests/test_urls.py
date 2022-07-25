from django.test import TestCase, Client
from django.contrib.auth import get_user_model

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

    def setUp(self) -> None:
        #  Создание неавторизованного пользователя
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client(self):
        '''Какие страницы доступны неавторизованному пользователю '''
        urls = {
            '/': 200,
            f'/group/{self.group.slug}/': 200,
            f'/posts/{1}/': 200,
            f'/profile/{self.user.username}/': 200,
            '/create/': 302,
            f'/posts/{1}/edit/': 302
        }
        for url, response_code in urls.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(response_code, status_code)

    def test_authorized_client(self):
        '''Какие страницы доступны авторизованному пользователю '''
        #  Если пользователь авторизован,
        #  и является автором поста - должны быть доступны все страницы
        if self.post.author == self.user.username:
            urls = {
                '/': 200,
                f'/group/{self.group.slug}/': 200,
                f'/posts/{1}/': 200,
                f'/profile/{self.user.username}/': 200,
                '/create/': 200,
                f'/posts/{1}/edit/': 200
            }
            for url, response_code in urls.items():
                with self.subTest(url=url):
                    status_code = self.authorized_client.get(url).status_code
                    self.assertEqual(response_code, status_code)
        #  Если пользователь не является автором поста
        #  должна быть недоступна страница редактирования поста
        else:
            urls = {
                '/': 200,
                f'/group/{self.group.slug}/': 200,
                f'/posts/{1}/': 200,
                f'/profile/{self.user.username}/': 200,
                '/create/': 200,
                f'/posts/{1}/edit/': 302
            }
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
            f'/posts/{1}/edit/': '/auth/login/?next=/posts/1/edit/'
        }
        for url, template in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, template)
