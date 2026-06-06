"""
Retourenschein-PDF Erstellung.
Nutzt xhtml2pdf (bereits für Rechnungen vorhanden).
Wird bei Genehmigung eines ReturnRequest automatisch aufgerufen.
"""
import os
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone


class ReturnLabelService:

    @staticmethod
    def generate_label(return_request):
        """
        Generiert PDF-Retourenschein für einen genehmigten ReturnRequest.
        Speichert unter MEDIA_ROOT/return_labels/ und setzt return_label_url.
        Gibt die URL zurück oder None bei Fehler.
        """
        try:
            from xhtml2pdf import pisa
        except ImportError:
            # xhtml2pdf nicht installiert — überspringen
            return None

        try:
            ctx = {
                'rr':      return_request,
                'order':   return_request.order,
                'user':    return_request.user,
                'now':     timezone.now(),
                'company': {
                    'name':    getattr(settings, 'COMPANY_NAME', 'Joel Digitals'),
                    'address': getattr(settings, 'COMPANY_ADDRESS', ''),
                    'zip':     getattr(settings, 'COMPANY_ZIP', ''),
                    'city':    getattr(settings, 'COMPANY_CITY', ''),
                    'email':   getattr(settings, 'SUPPORT_EMAIL', 'support@joel-digitals.de'),
                },
            }
            html = render_to_string('apps/return_label_pdf.html', ctx)
            buf = BytesIO()
            status = pisa.CreatePDF(html, dest=buf, encoding='UTF-8')

            if status.err:
                return None

            filename = f'return_label_{return_request.id:05d}.pdf'
            media_dir = os.path.join(settings.MEDIA_ROOT, 'return_labels')
            os.makedirs(media_dir, exist_ok=True)

            with open(os.path.join(media_dir, filename), 'wb') as f:
                f.write(buf.getvalue())

            url = f'{settings.MEDIA_URL}return_labels/{filename}'
            return_request.return_label_url = url
            return_request.save(update_fields=['return_label_url', 'updated_at'])
            return url

        except Exception as e:
            print(f'[ReturnLabelService] Fehler: {e}')
            return None
