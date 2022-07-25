from django.contrib import admin

from posts.models import Post, Group


class PostAdmin(admin.ModelAdmin):
    '''Админка
       Отвечает за то, что мы видим
       и с чем мы можем взаимодействовать в админке'''
    list_display = (  # поля, которые должны отображаться в админке
        'pk',  # уникальный идентификатор записи в базе данных
        'text',  # содержимое поля text каждого поста
        'pub_date',  # дата публикации
        'author',  # автор поста
        'group',)  # к какой группе принадлежит пост

    # перечисленные в list_editable поля будут отображаться в виде
    # виджетов формы на странице списка изменений,
    # позволяя пользователям редактировать их
    list_editable = ('group',)
    search_fields = ('text',)  # интерфейс для поиска по тексту постов
    list_filter = ('pub_date',)  # возможность фильтрации по дате
    empty_value_display = '-пусто-'  # где пусто — там будет эта строка


# регистрация моделей
admin.site.register(Post, PostAdmin)
admin.site.register(Group)
