from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from webinars.models import Webinar, WebinarRegistration


class Command(BaseCommand):
    help = 'Sendet Webinar-Erinnerungen mit Beitrittslink an registrierte Teilnehmer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Erinnerung X Stunden vor Webinar-Beginn senden (Default: 1)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Auch wenn reminder_sent bereits True ist'
        )
        parser.add_argument(
            '--webinar-id',
            type=int,
            help='Nur für ein bestimmtes Webinar (ID)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        force = options['force']
        webinar_id = options.get('webinar_id')

        now = timezone.now()
        window_start = now + timedelta(hours=hours - 0.25)
        window_end = now + timedelta(hours=hours + 0.25)

        webinars = Webinar.objects.filter(
            is_active=True,
            date_time__gte=window_start,
            date_time__lte=window_end,
        )
        if webinar_id:
            webinars = webinars.filter(id=webinar_id)

        sent = 0
        for webinar in webinars:
            registrations = WebinarRegistration.objects.filter(
                webinar=webinar,
                status='registered',
            )
            if not force:
                registrations = registrations.filter(reminder_sent=False)

            for reg in registrations:
                ctx = {
                    'user': reg.user,
                    'webinar': webinar,
                }
                html = render_to_string('emails/webinar_reminder.html', ctx)
                msg = EmailMultiAlternatives(
                    subject=f"🔔 Erinnerung: {webinar.title} beginnt bald!",
                    body=f"Hallo {reg.user.first_name or reg.user.username},\n\ndas Webinar '{webinar.title}' beginnt in Kürze.\n\nTermin: {webinar.date_time.strftime('%d.%m.%Y um %H:%M')} Uhr\n\n{('Beitrittslink: ' + webinar.meeting_url) if webinar.meeting_url else ''}\n\nViele Grüße,\nDein Joel Digitals Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[reg.user.email],
                )
                msg.attach_alternative(html, "text/html")
                try:
                    msg.send()
                    reg.reminder_sent = True
                    reg.save(update_fields=['reminder_sent'])
                    sent += 1
                except Exception as e:
                    self.stderr.write(f"Fehler bei User {reg.user.id}: {e}")

        self.stdout.write(f"{sent} Erinnerung(en) versendet.")
