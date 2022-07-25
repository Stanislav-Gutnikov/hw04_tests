from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # создаем тестового пользователя
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(  # создаем тестовую группу
            title='Тестовый заголовок',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(  # создаем тестовый пост
            text='Тестовый текст поста',
            pub_date='Тестовая дата публикации',
            author=cls.user,
        )

    def test_models_have_correct_object_name(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)
