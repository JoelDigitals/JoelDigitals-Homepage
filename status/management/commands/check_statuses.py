from django.core.management.base import BaseCommand
from status.models import App, AppStatus
import requests
import time


class Command(BaseCommand):
    help = "Prüft alle aktiven Apps und speichert den Status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Alle 3 Minuten wiederholen (für Dauereinsatz)",
        )

    def check_app(self, app):
        try:
            start = time.time()
            response = requests.get(app.server_url, timeout=10)
            duration = int((time.time() - start) * 1000)
            if response.status_code == 200:
                return "online", duration
            return "offline", None
        except Exception:
            return "offline", None

    def handle(self, *args, **options):
        self.check_all()
        if options["loop"]:
            self.stdout.write("Wiederhole alle 180 Sekunden...")
            while True:
                time.sleep(180)
                self.check_all()

    def check_all(self):
        apps = App.objects.filter(is_active=True)
        for app in apps:
            status, duration = self.check_app(app)
            AppStatus.objects.create(
                app=app,
                status=status,
                response_time_ms=duration,
                message="Automatische Prüfung",
            )
            self.stdout.write(f"{app.name}: {status}")
