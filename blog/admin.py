from django.contrib import admin
from .models import BlogPost, BlogCategory, Comment

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title_de', 'title_en', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'created_at', 'categories')
    search_fields = ('title_de', 'title_en', 'content_de', 'content_en')
    prepopulated_fields = {"title_en": ("title_de",)}
    filter_horizontal = ('categories',)
    
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
