from django.contrib import admin
from .models import BlogPost, BlogCategory, Comment

from django.utils.html import format_html

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title_de', 'title_en', 'is_published', 'ai_badge', 'created_at', 'updated_at')
    list_filter = ('is_published', 'main_image_ai_generated', 'created_at', 'categories')
    search_fields = ('title_de', 'title_en', 'content_de', 'content_en')
    prepopulated_fields = {"title_en": ("title_de",)}
    filter_horizontal = ('categories',)

    def ai_badge(self, obj):
        if obj.main_image_ai_generated:
            return format_html(
                '<span style="background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; '
                'padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">AI</span>'
            )
        return "—"
    ai_badge.short_description = "KI-Bild"
    
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
