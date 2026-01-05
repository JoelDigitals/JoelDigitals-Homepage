from django.shortcuts import render, redirect
from django.db.models import Avg
from .models import Review, Testimonial, GoogleReview
from .forms import ReviewForm

def review_page(request):
    reviews = Review.objects.filter(approved=True)
    testimonials = Testimonial.objects.filter(active=True)
    google_reviews = GoogleReview.objects.all()

    average_rating = reviews.aggregate(avg=Avg("rating"))["avg"]

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("review_thanks")
    else:
        form = ReviewForm()

    return render(request, "reviews/reviews.html", {
        "reviews": reviews,
        "testimonials": testimonials,
        "google_reviews": google_reviews,
        "average_rating": average_rating,
        "form": form,
    })


def review_thanks(request):
    return render(request, "reviews/thanks.html")
