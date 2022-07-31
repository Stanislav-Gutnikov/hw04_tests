from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm

from posts.models import Group, Post

User = get_user_model()


class CreateNewPostForm(TestCase):
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
        cls.form = PostForm()
        cls.form_data = {
            'text': 'something',
            'group': cls.group.id
        }

    def setUp(self) -> None:
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post3 = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый без группы пост',
        )

    def test_create_post(self):
        '''Авторизованный пользователь может создать пост
           Пост сохраняется в БД''
           Проверка группы и текста нового поста'''
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        Post.objects.all().delete()
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        # перенаправляет ли авторизованного пользователя на страницу профиля
        # после создания поста
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, self.form_data['text'])
        self.assertEqual(post.group.id, self.form_data['group'])

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
        cls.post_id_kwargs = {'post_id': cls.post.id}
        cls.form = PostForm()
        cls.form_data = {
            'group': cls.group.id,
            'text': 'New something'
        }

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
            reverse('posts:post_edit', kwargs=self.post_id_kwargs),
            data=self.form_data,
            follow=True
        )
        # сохранились ли новые данные в БД
        # совпадает ли текст отредактированного поста в БД
        # с новым текстом из заполненной формы
        post = Post.objects.get()
        self.assertEqual(post.text, self.form_data['text'])
        self.assertEqual(post.group.id, self.form_data['group'])

    def test_post_edit_authorized_user_alien_post(self):
        '''Авторизованный пользователь не может отредактировать чужой пост.'''
        response = self.authorized_client_alien.post(
            reverse('posts:post_edit', kwargs=self.post_id_kwargs),
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
            'posts:post_detail', kwargs=self.post_id_kwargs))
