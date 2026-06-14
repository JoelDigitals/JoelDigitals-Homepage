# blog/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Count, F
from django.utils import timezone
from django.conf import settings
from django import forms
from .models import BlogPost, BlogCategory, Comment, BlogViewTracking
from .forms import BlogPostForm, BlogCategoryForm


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Schreibe einen Kommentar...'})
        }


def is_blog_editor(user):
    return user.is_authenticated and user.groups.filter(name='Marketing').exists()


from django.utils import timezone
from django.core.paginator import Paginator
from django.db import models

def blog_list(request):
    lang = request.LANGUAGE_CODE
    now = timezone.now()

    categories_with_posts = BlogCategory.objects.filter(
        posts__is_published=True,
        posts__published_at__lte=now
    ).distinct()

    category_filters = request.GET.getlist("category")

    if category_filters:
        posts = BlogPost.objects.filter(
            is_published=True,
            published_at__lte=now,
            categories__id__in=category_filters
        ).distinct().order_by("-published_at", "-created_at")
    else:
        posts = BlogPost.objects.filter(
            is_published=True,
            published_at__lte=now
        ).order_by("-published_at", "-created_at")

    # Sprachabhängiger Titel & Teaser
    for post in posts:
        post.title = post.title_en if lang == "en" else post.title_de
        post.teaser_text = (post.content_en if lang == "en" else post.content_de)[:250]

    paginator = Paginator(posts, 18)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "blog/blog_list.html", {
        "posts": page_obj,
        "page_obj": page_obj,
        "categories_with_posts": categories_with_posts,
        "category_filters": category_filters,
        "lang": lang,
    })

def blog_detail_by_pk(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    return redirect("blog_detail", slug=post.slug)


def blog_detail(request, slug):
    lang = request.LANGUAGE_CODE
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    post.views += 1
    post.save(update_fields=["views"])

    today = timezone.now().date()
    tracking, _ = BlogViewTracking.objects.get_or_create(post=post, date=today)
    tracking.count = models.F('count') + 1
    tracking.save(update_fields=['count'])

    comments = post.comments.order_by("-created_at")
    form = CommentForm()

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect("blog_detail", slug=slug)

    related_posts = (
        BlogPost.objects.filter(is_published=True)
        .exclude(pk=post.pk)
        .annotate(same_categories=Count("categories"))
        .order_by("-same_categories", "-created_at")[:3]
    )

    # Sprachabhängiger Inhalt
    post.title = post.title_en if lang == "en" else post.title_de
    post.content = post.content_en if lang == "en" else post.content_de

    # Sprachabhängige Titel und Teaser für verwandte Beiträge
    for related in related_posts:
        related.title = related.title_en if lang == "en" else related.title_de
        related.teaser_text = (
            (related.content_en if lang == "en" else related.content_de)[:180] + "..."
        )

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
    
    # Nur die nötigsten Felder laden
    posts = BlogPost.objects.all().only(
        'id', 'title_de', 'title_en', 'created_at', 
        'is_published', 'teaser_image', 'views'
    ).prefetch_related('categories').order_by('-created_at')
    
    lang = request.LANGUAGE_CODE
    for post in posts:
        post.title = post.title_en if lang == "en" else post.title_de
        # Teaser OHNE den vollen Content zu laden
        post.teaser_text = ""  # Erstmal leer lassen zum Testen
    
    return render(request, 'blog/admin_blog.html', {
        'posts': posts,
        'user_groups': user_groups
    })

@user_passes_test(lambda u: u.is_staff or u.groups.filter(name="BlogEditor").exists())
def blog_create(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            if blog_post.is_published and not blog_post.published_at:
                blog_post.published_at = timezone.now()
            
            # Priorisierung: Wenn ImgBB URL vorhanden, teaser_image löschen
            if blog_post.main_image_url:
                blog_post.teaser_image = None
            
            blog_post.save()
            form.save_m2m()
            return redirect('admin_blog')
    else:
        form = BlogPostForm()

    return render(request, 'blog/blog_form.html', {
        'form': form,
        'action': 'Erstellen',
        'user_groups': user_groups,
        'IMGBB_API_KEY': settings.IMGBB_API_KEY,  # Aus settings.py
    })

@user_passes_test(is_blog_editor)
def blog_edit(request, pk):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            blog_post = form.save(commit=False)
            
            # Priorisierung beibehalten
            if blog_post.main_image_url:
                blog_post.teaser_image = None
                
            blog_post.save()
            return redirect('admin_blog')
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'blog/blog_form.html', {
        'form': form,
        'action': 'Bearbeiten',
        'user_groups': user_groups,
        'IMGBB_API_KEY': settings.IMGBB_API_KEY,
    })

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