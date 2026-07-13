from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from main.models import UserProfile


class Command(BaseCommand):
    help = "Sendet Marketing-E-Mails an alle opt-in Nutzer"

    def add_arguments(self, parser):
        parser.add_argument('subject', type=str, help='Betreff der E-Mail')
        parser.add_argument('--html', type=str, required=True, help='HTML-Datei mit dem Inhalt')
        parser.add_argument('--subtitle', type=str, default='', help='Untertitel')
        parser.add_argument('--preview', action='store_true', help='Nur Vorschau ausgeben, keine E-Mails senden')
        parser.add_argument('--dry-run', action='store_true', help='Nur Anzahl der Empfänger anzeigen')

    def handle(self, *args, **options):
        subject = options['subject']
        html_file = options['html']
        subtitle = options['subtitle']

        if not html_file.endswith('.html'):
            html_file = html_file + '.html'

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except FileNotFoundError:
            with open(f'main/templates/emails/{html_file}', 'r', encoding='utf-8') as f:
                raw_content = f.read()

        recipients = UserProfile.objects.filter(marketing_opt_in=True)
        count = recipients.count()

        if not count:
            self.stdout.write(self.style.WARNING('Keine Empfänger gefunden (alle haben sich abgemeldet).'))
            return

        if options['preview'] or options['dry_run']:
            self.stdout.write(self.style.SUCCESS(f'{count} Empfänger würden die E-Mail erhalten'))
            if options['preview']:
                sample = recipients.first()
                self.stdout.write(f'\nBeispiel-Empfänger: {sample.user.email}')
                self.stdout.write(f'Betreff: {subject}')
                self.stdout.write(f'=== Inhalt (Auszug) ===\n{raw_content[:500]}...')
            return

        confirm = input(f'\n{count} E-Mail(s) senden? (ja/nein): ')
        if confirm.lower() != 'ja':
            self.stdout.write(self.style.WARNING('Abgebrochen.'))
            return

        site_url = 'https://joel-digitals.de'
        sent = 0
        errors = 0

        for profile in recipients:
            try:
                unsubscribe_url = f'{site_url}{reverse("unsubscribe")}?token={profile.marketing_token}'
                html_content = render_to_string('emails/marketing.html', {
                    'subject': subject,
                    'subtitle': subtitle,
                    'content': raw_content,
                    'site_url': site_url,
                    'unsubscribe_url': unsubscribe_url,
                })
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[profile.user.email],
                )
                email.attach_alternative(html_content, 'text/html')
                email.send(fail_silently=False)
                sent += 1

                if sent % 50 == 0:
                    self.stdout.write(f'  ... {sent}/{count} gesendet')

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Fehler bei {profile.user.email}: {e}'))
                errors += 1

        self.stdout.write(self.style.SUCCESS(f'\nFertig! {sent} E-Mail(s) gesendet, {errors} Fehler.'))
