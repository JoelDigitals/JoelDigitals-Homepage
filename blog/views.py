# blog/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import BlogPost, BlogCategory
from .forms import BlogPostForm, BlogCategoryForm

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Count
from .models import BlogPost, BlogCategory, Comment
from .forms import BlogPostForm, BlogCategoryForm
from django import forms


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Schreibe einen Kommentar...'})
        }


def is_blog_editor(user):
    return user.is_authenticated and user.groups.filter(name='Marketing').exists()


def blog_list(request):
    lang = request.LANGUAGE_CODE  # automatisch ermittelt, z. B. 'de' oder 'en'
    categories_with_posts = BlogCategory.objects.filter(posts__is_published=True).distinct()
    category_filters = request.GET.getlist("category")

    if category_filters:
        posts = BlogPost.objects.filter(is_published=True, categories__id__in=category_filters).distinct().order_by("-created_at")
    else:
        posts = BlogPost.objects.filter(is_published=True).order_by("-created_at")

    # Titel je nach Sprache
    for post in posts:
        post.title = post.title_en if lang == "en" else post.title_de
        post.teaser_text = (post.content_en if lang == "en" else post.content_de)[:250]

    return render(request, "blog/blog_list.html", {
        "posts": posts,
        "categories_with_posts": categories_with_posts,
        "category_filters": category_filters,
        "lang": lang,
    })


def blog_detail(request, pk):
    lang = request.LANGUAGE_CODE
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    post.views += 1
    post.save(update_fields=["views"])

    comments = post.comments.order_by("-created_at")
    form = CommentForm()

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect("blog:blog_detail", pk=pk)

    related_posts = (
        BlogPost.objects.filter(is_published=True)
        .exclude(pk=pk)
        .annotate(same_categories=Count("categories"))
        .order_by("-same_categories", "-created_at")[:3]
    )

    # Sprachabhängiger Inhalt
    post.title = post.title_en if lang == "en" else post.title_de
    post.content = post.content_en if lang == "en" else post.content_de

    return render(request, "blog/blog_detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
        "related_posts": related_posts,
        "lang": lang,
    })



@user_passes_test(is_blog_editor)
def admin_blog(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'blog/admin_blog.html', {
        'posts': posts,
        'user_groups': user_groups
    })

@user_passes_test(is_blog_editor)
def blog_create(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_blog')
    else:
        form = BlogPostForm()
    return render(request, 'blog/blog_form.html', {
        'form': form,
        'action': 'Erstellen',
        'user_groups': user_groups
    })

@user_passes_test(is_blog_editor)
def blog_edit(request, pk):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('admin_blog')
    else:
        form = BlogPostForm(instance=post)

    context = {
        'form': form,
        'action': 'Bearbeiten',
        'user_groups': user_groups,
    }
    return render(request, 'blog/blog_form.html', context)

@user_passes_test(is_blog_editor)
def blog_delete(request, pk):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        post.delete()
        return redirect('admin_blog')

    context = {
        'post': post,
        'user_groups': user_groups,
    }
    return render(request, 'blog/blog_confirm_delete.html', context)

@user_passes_test(is_blog_editor)
def create_category(request):
    
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_blog')
    else:
        form = BlogCategoryForm()
    return render(request, 'blog/category_form.html', {'form': form, 'action': 'Erstellen'})

@user_passes_test(is_blog_editor)
def edit_category(request, pk):
    category = get_object_or_404(BlogCategory, pk=pk)
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin_blog')
    else:
        form = BlogCategoryForm(instance=category)
    return render(request, 'blog/category_form.html', {'form': form, 'action': 'Bearbeiten'})

@user_passes_test(is_blog_editor)
def delete_category(request, pk):
    category = get_object_or_404(BlogCategory, pk=pk)
    category.delete()
    return redirect('admin_blog')

@user_passes_test(is_blog_editor)
def list_categories(request):
    categories = BlogCategory.objects.all()
    return render(request, 'blog/category_list.html', {'categories': categories})