# blog/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import BlogPost, BlogCategory
from .forms import BlogPostForm, BlogCategoryForm

def is_blog_editor(user):
    return user.is_authenticated and user.groups.filter(name='Marketing').exists()



def blog_list(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    # Holen wir uns alle Kategorien, die Blog-Beiträge enthalten
    categories_with_posts = BlogCategory.objects.filter(posts__isnull=False)

    # Überprüfen, ob eine Filterung nach Kategorien erfolgt
    category_filters = request.GET.getlist('category')  # .getlist() holt alle ausgewählten Kategorien

    if category_filters:
        # Wir filtern die Posts, die eine der ausgewählten Kategorien enthalten
        posts = BlogPost.objects.filter(is_published=True, categories__id__in=category_filters).distinct().order_by('-created_at')
    else:
        # Wenn keine Kategorie ausgewählt ist, zeigen wir alle Posts an
        posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')

    return render(request, 'blog/blog_list.html', {
        'posts': posts,
        'categories_with_posts': categories_with_posts,
        'category_filters': category_filters
    })

def blog_detail(request, pk):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    return render(request, 'blog/blog_detail.html', {
        'post': post,
        'user_groups': user_groups
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