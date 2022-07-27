from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class CreateNewPostForm(TestCase):
    form_data = {
        'title': 'First',
        'text': 'something'
    }

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user,
            group=cls.group
        )

    def setUp(self) -> None:
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        '''Авторизованный пользователь может создать пост
           Пост сохраняется в БД'''
        Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        # перенаправляет ли авторизованного пользователя на страницу профиля
        # после создания поста
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        # проверка по id поста, сохраняется ли пост в БД
        self.assertTrue(Post.objects.filter(
            id=2))
        # совпадает ли текст нового поста в БД с текстом из заполненной формы
        self.assertTrue(Post.objects.filter(
            text=self.form_data['text']))

    def test_create_post_guest_client(self):
        '''Не авторизованный пользователь не может создать пост.
           Его перенаправляет на страницу авторизации'''
        response = self.client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        login = reverse('users:login')
        new = reverse('posts:post_create')
        redirect = login + '?next=' + new
        # перенаправляет ли не авторизованного пользователя
        # на страницу авторизации, при попытке создать пост
        self.assertRedirects(response, redirect)


class PostEditForm(TestCase):
    form_data = {
        'title': 'New',
        'text': 'New something'
    }

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='lolo')
        cls.alien_user = User.objects.create_user(username='Alien')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user,
            group=cls.group
        )

    def setUp(self) -> None:
        #  Создание авторизованного пользователя, автор поста
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        #  Создание авторизованного пользователя
        self.authorized_client_alien = Client()
        self.authorized_client_alien.force_login(self.alien_user)

    def test_post_edit(self):
        '''Сохраняются ли изменения после редактирования поста
           Пользователь - автор поста'''
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=self.form_data,
            follow=True
        )
        # сохранились ли новые данные в БД
        # совпадает ли текст отредактированного поста в БД
        # с новым текстом из заполненной формы
        self.assertTrue(Post.objects.filter(
            text=self.form_data['text']
        ).exists())

    def test_post_edit_authorized_user_alien_post(self):
        '''Авторизованный пользователь не может отредактировать чужой пост.'''
        response = self.authorized_client_alien.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=self.form_data,
            follow=True
        )
        # не сохранились ли новые данные в БД
        self.assertFalse(Post.objects.filter(
            text=self.form_data['text']
        ).exists())
        # перенаправляет ли пользователя на страницу поста
        # при попытке отредактировать чужой пост
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': 1}))
