from reviews.utils import get_average_rating


def seo_data(request):
    rating = get_average_rating()
    return {
        'rating': rating,
    }
