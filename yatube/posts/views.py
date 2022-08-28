from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator


@cache_page(60 * 20)
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user_profile).order_by('-pub_date')
    user_posts_count = Post.objects.filter(author=user_profile).count()
    page_obj = paginator(request, post_list)
    following = request.user.is_authenticated and \
        Follow.objects.filter(
            user=request.user,
            author=user_profile
        ).exists()
    context = {'user_profile': user_profile,
               'page_obj': page_obj,
               'user_posts_count': user_posts_count,
               'following': following
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_detail = get_object_or_404(Post, pk=post_id)
    author_posts_count = post_detail.author.posts.count()
    form = CommentForm(add_comment(request, post_id))
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post_detail,
        'author_posts_count': author_posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


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


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    is_edit = True
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': is_edit, 'post': post}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, pk=post_id)
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
    return render(request, 'posts/follow.html', context)


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
