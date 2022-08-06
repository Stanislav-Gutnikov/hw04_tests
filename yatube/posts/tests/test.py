from tkinter import N
from urllib import response
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Follow

User = get_user_model()


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