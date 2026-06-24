"""
Service für automatisierte Versand- und Review-Email-Prozesse.

Ablauf:
  1. Admin sendet Registrierungscode → Status: 'In Delivery'
  2. 30 Minuten später: automatisch → Status: 'Delivered', Review-Email geplant
  3. 12–72 Stunden später (zufällig): Review-Email senden → Status: 'Finished'
"""
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
import random
from shop_ourapps.models import Order, OrderStatusLog, Purchase, PackageApp


class OrderAutomationService:
    """Verwaltet automatische Status-Updates und Email-Versand für Bestellungen."""

    @staticmethod
    def log_event(order, event_type, old_status=None, new_status=None, note=""):
        """Protokolliert ein Ereignis im OrderStatusLog."""
        OrderStatusLog.objects.create(
            order=order,
            event_type=event_type,
            old_status=old_status,
            new_status=new_status,
            note=note
        )

    # ─────────────────────────────────────────────────────────────────
    # 1. ZAHLUNG
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def set_paid(order):
        """
        Setzt Bestellstatus auf 'Paid'.
        Wird von Stripe/PayPal-Callbacks aufgerufen.
        Erstellt Purchase-Einträge für alle gekauften Apps/Pakete.
        """
        if order.status not in ('Paid', 'In Delivery', 'Delivered', 'Finished'):
            old_status = order.status
            order.status = 'Paid'
            order.save(update_fields=['status'])
            OrderAutomationService.log_event(
                order,
                'status_changed',
                old_status=old_status,
                new_status='Paid',
                note=f'Automatisch auf bezahlt gesetzt via {order.payment_method}'
            )

            # Purchase-Einträge für alle Artikel erstellen
            from shop_ourapps.models import Purchase, PackageApp
            for item in order.items.all():
                if item.package:
                    # Paket selbst verbuchen
                    Purchase.objects.create(
                        user=order.user,
                        package=item.package,
                        full_name=f"{order.first_name} {order.last_name}",
                        email=order.email,
                        address=order.address or "",
                        zip_code=order.zip_code or "",
                        city=order.city or "",
                        country="Deutschland",
                    )
                    # Jede enthaltene App einzeln verbuchen
                    for pa in PackageApp.objects.filter(package=item.package).select_related('app'):
                        Purchase.objects.create(
                            user=order.user,
                            app=pa.app,
                            full_name=f"{order.first_name} {order.last_name}",
                            email=order.email,
                            address=order.address or "",
                            zip_code=order.zip_code or "",
                            city=order.city or "",
                            country="Deutschland",
                        )
                elif item.app:
                    Purchase.objects.create(
                        user=order.user,
                        app=item.app,
                        full_name=f"{order.first_name} {order.last_name}",
                        email=order.email,
                        address=order.address or "",
                        zip_code=order.zip_code or "",
                        city=order.city or "",
                        country="Deutschland",
                    )

            return True
        return False

    @staticmethod
    def set_payment_status(order):
        """
        Für manuelle/nicht-online Zahlungen (Wallet, Lastschrift, Überweisung).
        """
        if order.payment_method not in ('stripe', 'paypal'):
            return OrderAutomationService.set_paid(order)
        return False

    # ─────────────────────────────────────────────────────────────────
    # 2. REGISTRIERUNGSCODE SENDEN → IN DELIVERY
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def mark_as_sent(order, registration_code, force=False):
        """
        Wird aufgerufen wenn Admin Registrierungscode-Mail abschickt.
        Setzt Zeitstempel + Status 'In Delivery'. force=True erlaubt Überschreiben.
        """
        now = timezone.now()
        # Nur blockieren wenn bereits 'In Delivery' oder weiter UND nicht force
        if not force and order.status in ('In Delivery', 'Delivered', 'Finished'):
            # Zeitstempel updaten aber Status lassen
            order.registration_code = registration_code
            order.registration_code_sent_at = now
            order.save(update_fields=['registration_code', 'registration_code_sent_at'])
            OrderAutomationService.log_event(
                order, 'registration_code_sent',
                note=f'Code erneut gesendet (Status beibehalten): {registration_code}'
            )
            return True

        order.registration_code = registration_code
        order.registration_code_sent_at = now
        order.status = 'In Delivery'
        order.save(update_fields=['registration_code', 'registration_code_sent_at', 'status'])
        OrderAutomationService.log_event(
            order, 'registration_code_sent',
            new_status='In Delivery',
            note=f'Registrierungscode gesendet: {registration_code}'
        )
        return True

    # ─────────────────────────────────────────────────────────────────
    # 3. AUTO-DELIVERY (30 min nach Registrierungscode-Versand)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def auto_deliver_after_30_minutes():
        """
        Findet alle 'In Delivery'-Bestellungen, deren Code vor >= 30 Min gesendet wurde,
        und markiert sie als 'Delivered'. Plant danach die Review-Email (12–72h).
        """
        thirty_minutes_ago = timezone.now() - timedelta(minutes=30)

        orders_to_deliver = Order.objects.filter(
            registration_code_sent_at__lte=thirty_minutes_ago,
            delivered_at__isnull=True,
            status='In Delivery'
        )

        count = 0
        for order in orders_to_deliver:
            old_status = order.status
            order.status = 'Delivered'
            order.delivered_at = timezone.now()
            order.save(update_fields=['status', 'delivered_at'])

            # Plane Review-Email (12–72h zufällig)
            order.schedule_review_email()

            OrderAutomationService.log_event(
                order,
                'auto_delivered',
                old_status=old_status,
                new_status='Delivered',
                note='Automatisch nach 30 Minuten als geliefert markiert'
            )
            OrderAutomationService.log_event(
                order,
                'review_email_scheduled',
                note=f'Review-Email geplant für: {order.review_email_scheduled_for}'
            )
            count += 1

        return count

    # ─────────────────────────────────────────────────────────────────
    # 4. REVIEW-EMAIL SENDEN → FINISHED
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def send_review_emails():
        """
        Versendet Review-Emails für alle Bestellungen, deren Planzeit erreicht wurde.
        Markiert Bestellung danach als 'Finished'.
        """
        now = timezone.now()

        orders_for_review = Order.objects.filter(
            review_email_scheduled_for__lte=now,
            review_email_sent_at__isnull=True,
            status='Delivered'
        )

        count = 0
        for order in orders_for_review:
            try:
                OrderAutomationService._send_review_email(order)
                count += 1
            except Exception as e:
                print(f"[AutoReview] Fehler für Bestellung #{order.id}: {e}")
        return count

    @staticmethod
    def _send_review_email(order):
        """Interner Versand einer einzelnen Review-Email + Finished-Status."""
        context = {
            'order': order,
            'user_name': order.first_name,
            'order_id': order.id,
        }

        html_message = render_to_string('emails/review_request.html', context)
        subject = "⭐ Dein Feedback ist uns wichtig! | Your feedback matters to us!"

        email = EmailMultiAlternatives(
            subject,
            f"Bewertungsanfrage für Bestellung #{order.id}",
            settings.DEFAULT_FROM_EMAIL,
            [order.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

        # Status → Finished + Zeitstempel
        order.review_email_sent_at = timezone.now()
        order.status = 'Finished'
        order.save(update_fields=['review_email_sent_at', 'status'])

        OrderAutomationService.log_event(
            order,
            'review_email_sent',
            old_status='Delivered',
            new_status='Finished',
            note=f'Review-Email versendet an {order.email} → Status: Finished'
        )

    # ─────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_pending_orders_stats():
        thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
        now = timezone.now()
        return {
            'pending_delivery': Order.objects.filter(
                registration_code_sent_at__lte=thirty_minutes_ago,
                delivered_at__isnull=True,
                status='In Delivery'
            ).count(),
            'pending_review': Order.objects.filter(
                review_email_scheduled_for__lte=now,
                review_email_sent_at__isnull=True,
                status='Delivered'
            ).count(),
        }
