from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import CASHE_TIME

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow_index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@cache_page(CASHE_TIME)
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


def post_detail(request, post_id):
    post_detail = get_object_or_404(Post, id=post_id)
    author_posts_count = post_detail.author.posts.count()
    form = CommentForm(add_comment(request, post_id))
    comments = post_detail.comments.all()
    context = {
        'author_posts_count': author_posts_count,
        'comments': comments,
        'form': form,
        'post': post_detail,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True, 'post': post}
    return render(request, 'posts/create_post.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    user_posts_count = post_list.count()
    page_obj = paginator(request, post_list)
    following = author.following.filter(user__id=request.user.id).exists()
    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
        'user_posts_count': user_posts_count,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_follow(request, username):
    ''' Функция подписки на автора. '''
    follower = Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).count()
    if request.user.username != username and not follower:
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username),
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(author=author, user=request.user).delete()
    return redirect('posts:profile', username=username)
