import sys
import os
from django.core.asgi import get_asgi_application

# Der Pfad zu den Django-Einstellungen (ersetze 'deinprojektname' mit dem tatsächlichen Namen deines Projekts)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deinprojektname.settings")  # Ersetze deinprojektname mit deinem tatsächlichen Projektnamen

# ASGI-Anwendung von Django holen
app = get_asgi_application()
