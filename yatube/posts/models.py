from django.db import models

from django.contrib.auth import get_user_model

from core.models import CreatedModel


User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='group',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относится пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Добавьте к посту картинку'
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарий',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='folowwer',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='folowwing',
        verbose_name='Автор'
    )

    def __str__(self):
        return self.text[:15]
