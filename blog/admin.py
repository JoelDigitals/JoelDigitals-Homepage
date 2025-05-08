from django.contrib import admin
from .models import BlogPost, BlogCategory

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at', 'categories')
    search_fields = ('title', 'content')
    filter_horizontal = ('categories',)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)