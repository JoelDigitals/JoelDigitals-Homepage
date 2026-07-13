from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from shop_ourapps.models import Order, ShipmentTracking

from .services.push import send_push_notification

ORDER_STATUS_PUSH_MESSAGES = {
    'Paid': 'Deine Zahlung ist eingegangen - wir bereiten deine Bestellung vor.',
    'In Delivery': 'Deine Bestellung ist unterwegs.',
    'Delivered': 'Deine Bestellung wurde zugestellt.',
    'Finished': 'Deine Bestellung wurde abgeschlossen.',
    'Return': 'Deine Rücksendung wird bearbeitet.',
    'Canceled': 'Deine Bestellung wurde storniert.',
}


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
