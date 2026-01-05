from django.contrib import admin
from .models import Review, Testimonial, GoogleReview

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "approved", "created_at")
    list_filter = ("approved", "rating")
    search_fields = ("name", "text")
    actions = ["approve_reviews"]

    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "active")
    list_filter = ("active",)


@admin.register(GoogleReview)
class GoogleReviewAdmin(admin.ModelAdmin):
    list_display = ("author_name", "rating", "time")
