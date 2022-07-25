from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post

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

    def setUp(self) -> None:
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': f'{self.post.author}'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={
                'post_id': 1}): 'posts/post_create.html'
        }
        for reverse_name, template in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_context(self):
        context = {
            reverse('posts:index'): self.post,
            reverse('posts:group_list', kwargs={
                'slug': 'test-slug'}): self.post,
            reverse('posts:profile', kwargs={
                'username': f'{self.post.author}'}): self.post
        }
        for reverse_name, object in context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                page_object = response.context['page_obj'][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.pub_date, object.pub_date)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)

    def test_post_detail_uses_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        object = response.context['post']
        self.assertEqual(self.post.text, object.text)
        self.assertEqual(self.post.pub_date, object.pub_date)
        self.assertEqual(self.post.author, object.author)
        self.assertEqual(self.post.group, object.group)

    def test_post_form_uses_correct_context(self):
        context = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': 1})
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
            for i in range(13)
        ]

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(username='NoName1')
        #  Создание авторизованного пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_on_pages(self):
        '''Проверяем, корректно ли работает paginator'''
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
