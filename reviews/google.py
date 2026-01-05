# reviews/google.py
import requests
from django.utils import timezone
from .models import GoogleReview

def sync_google_reviews(api_key, place_id):
    """
    Lädt Google-Bewertungen für einen Place und speichert sie in der Datenbank,
    ohne doppelte Einträge zu erzeugen.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "reviews",
        "key": api_key,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Fehler beim Abrufen der Google Reviews: {response.status_code}")
        return

    data = response.json()
    reviews = data.get("result", {}).get("reviews", [])
    for review in reviews:
        # Google gibt die Zeit als UNIX timestamp (Sekunden seit Epoch)
        review_time = timezone.datetime.fromtimestamp(review["time"], tz=timezone.utc)

        # get_or_create nach author_name + Zeit, um Duplikate zu vermeiden
        obj, created = GoogleReview.objects.get_or_create(
            author_name=review["author_name"],
            time=review_time,
            defaults={
                "rating": review["rating"],
                "text": review.get("text", ""),
            }
        )
        if created:
            print(f"Neue Bewertung gespeichert: {review['author_name']} ({review['rating']}★)")
