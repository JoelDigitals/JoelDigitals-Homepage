# reviews/views.py
import math
from django.shortcuts import render, redirect
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from .models import Review, Testimonial, GoogleReview
from .forms import ReviewForm

def review_page(request):
    reviews = Review.objects.filter(approved=True)
    testimonials = Testimonial.objects.filter(active=True)
    google_reviews = GoogleReview.objects.all()

    average_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    
    # Sterne-Display berechnen
    star_data = {'full': [], 'half': False, 'empty': []}
    
    if average_rating:
        full_stars = int(average_rating)  # 4.5 -> 4
        decimal_part = average_rating - full_stars  # 4.5 -> 0.5
        
        # Volle Sterne als Liste
        star_data['full'] = list(range(full_stars))  # [0, 1, 2, 3] für 4 Sterne
        
        # Halber Stern wenn >= 0.3
        if decimal_part >= 0.3:
            star_data['half'] = True
            empty_count = 5 - full_stars - 1
        else:
            empty_count = 5 - full_stars
        
        # Leere Sterne
        star_data['empty'] = list(range(empty_count))

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            send_mail(
                subject="Neue Bewertung eingegangen",
                message="Es gibt eine neue Bewertung auf der Webseite.",
                from_email=settings.COMPANY_EMAIL_NO_REPLY,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            return redirect("review_thanks")
    else:
        form = ReviewForm()

    return render(request, "reviews/reviews.html", {
        "reviews": reviews,
        "testimonials": testimonials,
        "google_reviews": google_reviews,
        "average_rating": average_rating,
        "star_data": star_data,
        "form": form,
    })

def review_thanks(request):
    return render(request, "reviews/thanks.html")
