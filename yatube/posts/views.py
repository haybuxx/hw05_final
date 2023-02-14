from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow

from .utils import get_context_page

SHORT_TEXT = 30
POSTS_NUMBER = 10


def index(request):
    posts = Post.objects.all()
    page_obj = get_context_page(request, posts, POSTS_NUMBER)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_context_page(request, group.posts.all(), POSTS_NUMBER)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_total_posts = author.posts.count()
    page_obj = get_context_page(request, author.posts.all(), POSTS_NUMBER)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    profile = author
    context = {
        'author': author,
        'author_total_posts': author_total_posts,
        'page_obj': page_obj,
        'following': following,
        'profile': profile
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_total_posts = post.author.posts.count()
    form = CommentForm()
    context = {
        'post': post,
        'author_total_posts': author_total_posts,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(reverse('posts:profile',
                            kwargs={'username': request.user}))


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if post.author != request.user:
        return redirect(reverse('posts:profile',
                                kwargs={'username': request.user}))
    if form.is_valid():
        post = form.save()
        return redirect(reverse('posts:post_detail',
                        kwargs={'post_id': post_id}))

    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': is_edit, 'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(reverse('posts:post_detail',
                        kwargs={'post_id': post_id}))
    return render(request, 'posts/post_detail.html', {'form': form,
                  'post': post})


@login_required
def follow_index(request):
    page_obj = get_context_page(request,
                                Post.objects.filter(
                                    author__following__user=request.user), 20)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user != get_object_or_404(User, username=username):
        Follow.objects.get_or_create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
