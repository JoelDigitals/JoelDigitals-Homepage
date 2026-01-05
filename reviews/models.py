from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.rating}★)"


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=120)
    position = models.CharField(max_length=120, blank=True)
    text = models.TextField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.customer_name


class GoogleReview(models.Model):
    author_name = models.CharField(max_length=200)
    rating = models.IntegerField()
    text = models.TextField(blank=True)
    profile_photo_url = models.URLField(blank=True)
    time = models.DateTimeField()

    def __str__(self):
        return f"{self.author_name} (Google)"
