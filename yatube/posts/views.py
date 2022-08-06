from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page

from posts.models import Post, Group, User, Follow
from posts.forms import CommentForm, PostForm, CommentForm


posts_on_page = 10


@cache_page(20)
def index(request):
    '''Функция главной страницы сайта
       Передает в posts/index.html запрос и словарь context
       Ограничивает кол-во постов на странице до 10
       Подключена навигация с помощью пагинатора'''
    posts = Post.objects.all()
    paginator = Paginator(posts, posts_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    '''Функция страницы с групповыми
       Передает в posts/group_list.html запрос и словарь context
       Ограничивает кол-во постов на странице до 10
       Подключена навигация с помощью пагинатора'''
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.all()
    paginator = Paginator(posts, posts_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
        'title': f'Посты группы "{group}"',
    }
    return render(request, template, context)


def profile(request, username):
    '''Функция профиля автора
       Передает в posts/profile.html кол-во постов автора
       Подключена навигация с помощью пагинатора'''
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, posts_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/profile.html'
    following = None
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user)
        context = {
            'author': author,
            'posts_count': posts.count,
            'page_obj': page_obj,
            'following': following
        }
    else:
        context = {
            'author': author,
            'posts_count': posts.count,
            'page_obj': page_obj
        }
    return render(request, template, context)


def post_detail(request, post_id):
    '''Функция одного отдельного поста
       Передает в posts/post_detail.html пост и кол-во
       постов автора'''
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all().select_related('author')
    form = CommentForm()
    num_posts = Post.objects.filter(author__username=post.author)
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'num_posts': num_posts.count
    }
    return render(request, template, context)


@login_required
def post_create(request):
    '''Функция создания поста
       Позволяет создать новый пост, если пользователь
       авторизован
       После создания поста пользователя перекидывает
       на профиль автора (свой профиль)
       Если пользователь не авторизован, в posts/post_create.html
       передается пустая форма нового поста'''
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(f'/profile/{post.author}/')
    form = PostForm()
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    '''Функция редактирования поста
       Позволяет редактировать существующий пост,
       имя пользователя совпадает с автором поста
       При успешном редактировании пользователя перекидывает
       в posts/post_detail.html
       В противном случае изменения не сохраняются
       и предлагается заполнить форму заново
       '''
    post = Post.objects.get(pk=post_id)
    if request.user == post.author:
        form = PostForm(
            request.POST or None,
            instance=post,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post.id)
        else:
            context = {
                'form': form,
                'post': post,
                'is_edit': True
            }
            return render(request, 'posts/post_create.html', context)
    else:
        return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/add_comment.html',
        {'form': form, 'post': post}
    )


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__folowwing__user=request.user)
    paginator = Paginator(posts, posts_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
