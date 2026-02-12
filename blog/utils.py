import requests
import base64
from django.conf import settings


def upload_to_imgbb(image_file):
    """
    Lädt ein Bild zu ImgBB hoch
    
    Args:
        image_file: Django UploadedFile object
        
    Returns:
        dict: Response mit URL und anderen Daten oder None bei Fehler
    """
    url = "https://api.imgbb.com/1/upload"
    
    # Bild in base64 konvertieren
    image_file.seek(0)  # Zurück zum Anfang der Datei
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    payload = {
        'key': settings.IMGBB_API_KEY,
        'image': image_data,
    }
    
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            return {
                'url': result['data']['url'],
                'display_url': result['data']['display_url'],
                'delete_url': result['data']['delete_url'],
                'thumb_url': result['data']['thumb']['url'],
                'medium_url': result['data'].get('medium', {}).get('url', result['data']['url']),
            }
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error uploading to ImgBB: {e}")
        return None