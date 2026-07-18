from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from contact.models import SupportTicket, TicketMessage
from shop_ourapps.models import Order, ShipmentTracking
from status.models import AppIssue, GlobalIssue

from .services.push import send_push_notification

TICKET_URL_TEMPLATE = "https://www.joel-digitals.de/de/app/support/{ticket_number}/"
ORDER_ADMIN_URL = "https://www.joel-digitals.de/de/app/admin-orders/"
STATUS_URL = "https://www.joel-digitals.de/de/app/status/"

ORDER_STATUS_PUSH_MESSAGES = {
    'Paid': 'Deine Zahlung ist eingegangen - wir bereiten deine Bestellung vor.',
    'In Delivery': 'Deine Bestellung ist unterwegs.',
    'Delivered': 'Deine Bestellung wurde zugestellt.',
    'Finished': 'Deine Bestellung wurde abgeschlossen.',
    'Return': 'Deine Rücksendung wird bearbeitet.',
    'Canceled': 'Deine Bestellung wurde storniert.',
}


def _sales_staff_user_ids():
    """Alle Sales-Mitarbeiter (Gruppe 'Selling' - gleiche Gruppe wie
    contact.views.is_Sales_Editor / shop_ourapps.views.order_admin)."""
    return list(
        User.objects.filter(groups__name='Selling').distinct().values_list('id', flat=True)
    )


@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    """Neue Bestellung -> Push ans Sales-Team (damit niemand eine eingehende
    Bestellung verpasst) UND an den Kunden (Bestaetigung, dass die Bestellung
    angekommen ist)."""
    if not created:
        return

    staff_recipients = _sales_staff_user_ids()
    if staff_recipients:
        send_push_notification(
            title=f"Neue Bestellung #{instance.pk}",
            message=f"{instance.first_name} {instance.last_name} - {instance.total_amount}€",
            user_ids=staff_recipients,
            url=ORDER_ADMIN_URL,
        )

    if instance.user_id:
        send_push_notification(
            title=f"Bestellung #{instance.pk}",
            message="Deine Bestellung ist eingegangen - wir kümmern uns darum.",
            user_ids=[instance.user_id],
        )


@receiver(pre_save, sender=Order)
def notify_order_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous_status = Order.objects.only('status').get(pk=instance.pk).status
    except Order.DoesNotExist:
        return

    if previous_status == instance.status:
        return

    message = ORDER_STATUS_PUSH_MESSAGES.get(instance.status)
    if not message:
        return

    send_push_notification(
        title=f"Bestellung #{instance.pk}",
        message=message,
        user_ids=[instance.user_id],
    )


@receiver(pre_save, sender=ShipmentTracking)
def _stash_previous_tracking_number(sender, instance, **kwargs):
    """Merkt sich den bisherigen Tracking-Code, um Updates von Neuanlagen zu unterscheiden."""
    if not instance.pk:
        instance._previous_tracking_number = None
        return
    try:
        instance._previous_tracking_number = ShipmentTracking.objects.only('tracking_number').get(pk=instance.pk).tracking_number
    except ShipmentTracking.DoesNotExist:
        instance._previous_tracking_number = None


@receiver(post_save, sender=ShipmentTracking)
def notify_shipment_tracking_update(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_tracking_number', None)
    if not created and previous == instance.tracking_number:
        return  # keine relevante Aenderung am Tracking-Code

    if created:
        message = f"Deine Bestellung ist unterwegs - {instance.get_carrier_display()} Tracking: {instance.tracking_number}"
    else:
        message = f"Neue Sendungsverfolgung: {instance.get_carrier_display()} Tracking: {instance.tracking_number}"

    send_push_notification(
        title=f"Bestellung #{instance.order_id}",
        message=message,
        user_ids=[instance.order.user_id],
    )


def _support_staff_user_ids():
    """Alle Support-Mitarbeiter (Gruppen 'Support' und 'Admin Support' - gleiche
    Gruppennamen wie in contact.views.is_Support_Editor/is_Support_Ticket_Admin)."""
    return list(
        User.objects.filter(groups__name__in=['Support', 'Admin Support'])
        .distinct()
        .values_list('id', flat=True)
    )


@receiver(post_save, sender=SupportTicket)
def notify_new_ticket(sender, instance, created, **kwargs):
    """Neues Ticket -> an den zugewiesenen Mitarbeiter (falls vorhanden) oder
    an das gesamte Support-Team pushen."""
    if not created:
        return

    recipients = [instance.assigned_to_id] if instance.assigned_to_id else _support_staff_user_ids()
    recipients = [r for r in recipients if r]
    if not recipients:
        return

    send_push_notification(
        title=f"Neues Ticket #{instance.ticket_number}",
        message=f"{instance.name}: {instance.subject}",
        user_ids=recipients,
        url=TICKET_URL_TEMPLATE.format(ticket_number=instance.ticket_number),
    )


@receiver(pre_save, sender=SupportTicket)
def _stash_previous_ticket_state(sender, instance, **kwargs):
    """Merkt sich Status/Zuweisung vor dem Speichern, um Aenderungen zu erkennen."""
    if not instance.pk:
        instance._previous_is_resolved = None
        instance._previous_assigned_to_id = None
        return
    try:
        previous = SupportTicket.objects.only('is_resolved', 'assigned_to_id').get(pk=instance.pk)
        instance._previous_is_resolved = previous.is_resolved
        instance._previous_assigned_to_id = previous.assigned_to_id
    except SupportTicket.DoesNotExist:
        instance._previous_is_resolved = None
        instance._previous_assigned_to_id = None


@receiver(post_save, sender=SupportTicket)
def notify_ticket_status_or_assignment_change(sender, instance, created, **kwargs):
    if created:
        return

    ticket_url = TICKET_URL_TEMPLATE.format(ticket_number=instance.ticket_number)

    previous_is_resolved = getattr(instance, '_previous_is_resolved', None)
    if previous_is_resolved is not None and previous_is_resolved != instance.is_resolved and instance.user_id:
        message = 'Dein Ticket wurde gelöst.' if instance.is_resolved else 'Dein Ticket wurde wieder geöffnet.'
        send_push_notification(
            title=f"Ticket #{instance.ticket_number}",
            message=message,
            user_ids=[instance.user_id],
            url=ticket_url,
        )

    previous_assigned_to_id = getattr(instance, '_previous_assigned_to_id', None)
    if instance.assigned_to_id and instance.assigned_to_id != previous_assigned_to_id:
        send_push_notification(
            title="Ticket zugewiesen",
            message=f"Dir wurde Ticket #{instance.ticket_number} zugewiesen - {instance.subject}",
            user_ids=[instance.assigned_to_id],
            url=ticket_url,
        )


@receiver(post_save, sender=TicketMessage)
def notify_ticket_reply(sender, instance, created, **kwargs):
    """Neue Nachricht im Ticket-Thread -> die jeweils andere Seite benachrichtigen
    (Kunde antwortet -> Support-Team; Support antwortet -> Kunde)."""
    if not created:
        return

    ticket = instance.ticket
    preview = instance.message[:120]
    ticket_url = TICKET_URL_TEMPLATE.format(ticket_number=ticket.ticket_number)

    if instance.sender_id == ticket.user_id:
        recipients = [ticket.assigned_to_id] if ticket.assigned_to_id else _support_staff_user_ids()
        recipients = [r for r in recipients if r]
        title = f"Neue Antwort - Ticket #{ticket.ticket_number}"
    else:
        if not ticket.user_id:
            return
        recipients = [ticket.user_id]
        title = f"Antwort zu deinem Ticket #{ticket.ticket_number}"

    if not recipients:
        return

    send_push_notification(
        title=title,
        message=preview,
        user_ids=recipients,
        url=ticket_url,
    )


@receiver(post_save, sender=AppIssue)
def notify_new_app_issue(sender, instance, created, **kwargs):
    """Neue Stoerung bei einer App -> Push nur an Nutzer, die diese App unter
    Einstellungen -> Stoerungsbenachrichtigungen abonniert haben."""
    if not created:
        return

    from .models import StatusSubscription

    recipients = list(
        StatusSubscription.objects.filter(app=instance.app).values_list('user_id', flat=True)
    )
    if not recipients:
        return

    send_push_notification(
        title=f"Störung: {instance.app.name}",
        message=instance.title_de,
        user_ids=recipients,
        url=STATUS_URL,
    )


@receiver(post_save, sender=GlobalIssue)
def notify_new_global_issue(sender, instance, created, **kwargs):
    """Neue globale Stoerung -> Push an alle Nutzer, die mindestens eine App
    abonniert haben (= generelles Interesse an Stoerungsbenachrichtigungen)."""
    if not created:
        return

    from .models import StatusSubscription

    recipients = list(
        StatusSubscription.objects.values_list('user_id', flat=True).distinct()
    )
    if not recipients:
        return

    send_push_notification(
        title="Globale Störung",
        message=instance.title_de,
        user_ids=recipients,
        url=STATUS_URL,
    )
