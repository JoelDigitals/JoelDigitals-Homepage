from django.shortcuts import render, get_object_or_404
from .models import BlogPost
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test

def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog/blog_list.html', {'posts': posts})

def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    return render(request, 'blog/blog_detail.html', {'post': post})

@staff_member_required
def admin_blog(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'blog/admin_blog.html', {'posts': posts})

