
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order
from .services.email_service import send_review_request, send_shipping_notification


@receiver(post_save, sender=Order)
def order_status_email(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == "In Delivery":
        send_shipping_notification(instance)

    if instance.status == "Delivered":
        send_review_request(instance)
