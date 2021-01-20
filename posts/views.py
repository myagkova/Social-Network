from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related("group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html", {
            "group": group,
            "page": page,
            "paginator": paginator
        }
    )


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            cache.clear()
            return redirect("index")
        return render(request, "posts/new.html", {"form": form})

    form = PostForm()
    return render(request, "posts/new.html", {"form": form, "is_edit": False})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_anonymous:
        following = False
    else:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    return render(
        request,
        "posts/profile.html", {
            "author": author,
            "page": page,
            "post_count": post_count,
            "paginator": paginator,
            "following": following,
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    posts_count = post.author.posts.count()
    form = CommentForm()
    comments = Comment.objects.filter(post__id=post_id)
    return render(
        request, "posts/post.html", {
            "author": post.author,
            "post": post,
            "post_count": posts_count,
            "form": form,
            "comments": comments,
        }
    )


@ login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "posts/new.html", {"form": form, "post": post,
                                              "is_edit": True})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@ login_required
def add_comment(request, username, post_id):
    post = Post.objects.get(author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid:
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "posts/post.html", {"post": post, "form": form})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
        return redirect("profile", username=username)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect("profile", username=username)
    return redirect("profile", username=username)
