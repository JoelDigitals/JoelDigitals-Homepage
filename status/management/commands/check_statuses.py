from django.core.management.base import BaseCommand
from status.checker import check_all_apps
import time


class Command(BaseCommand):
    help = "Prüft alle aktiven Apps und speichert den Status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Alle 3 Minuten wiederholen (für Dauereinsatz)",
        )

    def handle(self, *args, **options):
        results = check_all_apps()
        for name, status in results:
            self.stdout.write(f"{name}: {status}")

        if options["loop"]:
            self.stdout.write("Wiederhole alle 180 Sekunden...")
            while True:
                time.sleep(180)
                results = check_all_apps()
                for name, status in results:
                    self.stdout.write(f"{name}: {status}")
