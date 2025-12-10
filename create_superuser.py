import os
import django
from django.contrib.auth.models import User

# Django Settings importieren
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joel_digitals.settings")

django.setup()

def create_superuser():
    username = 'JoelDigitals'  # Benutzername
    email = 'no-reply@joel-digitals.com'  # E-Mail-Adresse
    password = 'Jo240207!'  # Passwort

    # Überprüfen, ob der Superuser bereits existiert
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'Superuser {username} wurde erstellt!')
    else:
        print(f'Superuser {username} existiert bereits.')

if __name__ == "__main__":
    create_superuser()
