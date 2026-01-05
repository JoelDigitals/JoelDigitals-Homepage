from django.urls import path
from . import views

urlpatterns = [
    path("bewertungen/", views.review_page, name="reviews"),
    path("bewertungen/danke/", views.review_thanks, name="review_thanks"),
]
