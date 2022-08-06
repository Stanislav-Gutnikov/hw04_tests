import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


from posts.forms import PostForm, CommentForm
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateNewPostForm(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
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
            group=cls.group,
        )
        cls.form = PostForm()
        cls.form_data = {
            'text': 'Текст поста',
            'group': cls.group.id,
            'image': cls.uploaded,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        Post.objects.all().delete()
        response = self.authorized_client.post(
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
        self.assertEqual(post.image.name, 'posts/small.gif')

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostEditForm(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='lolo')
        cls.alien_user = User.objects.create_user(username='Alien')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test1-slug',
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
            'text': 'New',
            'group': cls.group.id,
            'image': cls.uploaded
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        request = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs=self.post_id_kwargs
        ))
        post = request.context.get('post')
        self.assertEqual(post.text, self.form_data['text'])
        self.assertEqual(post.group.id, self.form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

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


class PostCommentForm(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='lolo')
        cls.alien_user = User.objects.create_user(username='Alien')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user,
        )
        cls.post_id_kwargs = {'post_id': cls.post.id}
        cls.form = CommentForm()
        cls.form_data = {
            'text': 'New something'
        }

    def setUp(self) -> None:
        #  Создание авторизованного пользователя, автор поста
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        #  Создание авторизованного пользователя
        self.authorized_client_alien = Client()
        self.authorized_client_alien.force_login(self.alien_user)

    def test_guest_client_add_comment(self):
        '''Перенаправляет ли неавторизованного пользователя
           на страницу авторизации при попытке
           создать комментарий к записи'''
        response = self.client.post(
            reverse('posts:add_comment', kwargs=self.post_id_kwargs),
            data=self.form_data,
            follow=True
        )
        login = reverse('users:login')
        new = reverse('posts:add_comment', kwargs=self.post_id_kwargs)
        redirect = login + '?next=' + new
        self.assertRedirects(response, redirect)

    def test_success_comment_on_post_detail(self):
        '''Появился ли комментарий на странице поста
           Соответствует ли его содержимое ожидаемому'''
        self.assertEqual(self.post.comments.count(), 0)
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs=self.post_id_kwargs),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), 1)
        request = self.authorized_client.get(
            reverse('posts:post_detail', kwargs=self.post_id_kwargs)
        )
        obj = request.context['comments'][0]
        self.assertEqual(obj.text, self.form_data['text'])
