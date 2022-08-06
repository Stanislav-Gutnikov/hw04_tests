from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Follow

User = get_user_model()


class PostViewsTest(TestCase):
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
        cls.group_kwargs = {'slug': 'test-slug'}
        cls.author_kwargs = {'username': f'{cls.post.author}'}
        cls.post_id_kwargs = {'post_id': cls.post.id}

    def setUp(self) -> None:
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        '''Проверяем какие шаблоны используют views'''
        cache.clear()
        templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs=self.group_kwargs):
                'posts/group_list.html',
            reverse('posts:profile', kwargs=self.author_kwargs):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs=self.post_id_kwargs):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs=self.post_id_kwargs):
                'posts/post_create.html'
        }
        for reverse_name, template in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_context(self):
        '''Проверяем соответствует ли содержание словаря
           context ожидаемому'''
        cache.clear()
        context = {
            reverse('posts:index'): self.post,
            reverse('posts:group_list', kwargs=self.group_kwargs):
                self.post,
            reverse('posts:profile', kwargs=self.author_kwargs):
                self.post
        }
        for reverse_name, object in context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                page_object = response.context['page_obj'][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.pub_date, object.pub_date)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)
                self.assertEqual(page_object.image, object.image)

    def test_post_detail_uses_correct_context(self):
        '''Проверяем соответствует ли содержание словаря
           context ожидаемому на странице поста'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs=self.post_id_kwargs))
        object = response.context['post']
        self.assertEqual(self.post.text, object.text)
        self.assertEqual(self.post.pub_date, object.pub_date)
        self.assertEqual(self.post.author, object.author)
        self.assertEqual(self.post.group, object.group)

    def test_post_form_uses_correct_context(self):
        context = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs=self.post_id_kwargs)
        ]
        for reverse_name in context:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                object = response.context['form']
                self.assertIsInstance(
                    object.fields['text'], forms.fields.CharField)
                self.assertIsInstance(
                    object.fields['group'], forms.fields.ChoiceField)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.thirteen_test_posts = 13
        cls.user = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = [Post.objects.create(
            text='Тестовый текст поста' + str(i),
            pub_date='Тестовая дата публикации',
            author=cls.user,
            group=cls.group
        )
            for i in range(cls.thirteen_test_posts)
        ]

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(username='NoName1')
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_on_pages(self):
        '''Проверяем, корректно ли работает paginator'''
        cache.clear()
        first_page_len_posts = 10  # 10 постов на первой странице
        second_page_len_posts = 3  # 3 поста на второй
        context = {
            reverse(
                'posts:index'
            ): first_page_len_posts,
            reverse(
                'posts:index'
            ) + '?page=2': second_page_len_posts,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): first_page_len_posts,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2': second_page_len_posts,
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user.username}'}
            ): first_page_len_posts,
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user.username}'}
            ) + '?page=2': second_page_len_posts
        }
        for reverse_name, posts_count in context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10,
                # а на второй 3
                self.assertEqual(len(
                    response.context['page_obj']
                ), posts_count)


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Cache_tester')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user
        )

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        '''Проверка, работает ли кэш на главной странице'''
        response = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.create(
            text='some text',
            author=self.user
        )
        old_response = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(old_response, response)
        cache.clear()
        new_response = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(new_response, response)


class FollowViewsTest(TestCase):
    cache.clear()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create(username='Test_author')
        cls.user = User.objects.create(username='Follow_tester')
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.author
        )

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_follow_unfollow(self):
        '''Проверка, работает ли подписка и отписка от автора'''
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj']
        # пользователь не подписан,
        # значит на странице не должно быть постов автора
        self.assertEqual(len(context), 0)
        # Подписываемся на автора
        Follow.objects.create(user=self.user, author=self.author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        # пользователь подписан, значит должен видеть пост автора
        context = response.context['page_obj']
        self.assertEqual(len(context), 1)
        # Отписываемся
        Follow.objects.filter(user=self.user, author=self.author).delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj']
        # Проверяем, нет ли постов автора
        self.assertEqual(len(context), 0)
