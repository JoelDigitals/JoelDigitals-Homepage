from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import UserProfile


class Command(BaseCommand):
    help = "Erstellt UserProfile für alle User, die noch keines haben"

    def handle(self, *args, **options):
        users_without = []
        for user in User.objects.all():
            try:
                _ = user.userprofile
            except UserProfile.DoesNotExist:
                users_without.append(user)

        if not users_without:
            self.stdout.write(self.style.SUCCESS("Alle User haben bereits ein Profil."))
            return

        created = 0
        for user in users_without:
            UserProfile.objects.create(user=user)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} UserProfile(s) erstellt."))
