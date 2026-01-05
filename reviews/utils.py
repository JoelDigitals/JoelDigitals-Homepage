# reviews/utils.py
from django.db.models import Avg, Count
from .models import Review  # oder wo auch immer dein Review-Model ist

def get_average_rating():
    """
    Berechnet die Durchschnittsbewertung aller Reviews.
    Gibt ein Dictionary zurück mit: average, stars, count
    """
    result = Review.objects.aggregate(
        avg_rating=Avg('rating'),
        total_count=Count('id')
    )
    
    avg = result['avg_rating'] or 0.0
    count = result['total_count'] or 0
    
    return {
        'average': round(avg, 1),      # z.B. 4.5
        'stars': round(avg),           # z.B. 5 (für Sternen-Display)
        'count': count                 # z.B. 42
    }