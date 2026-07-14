from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def check_onesignal_sync(sender, request, user, **kwargs):
    profile = getattr(user, 'userprofile', None)
    if not profile:
        return
    now = timezone.now()
    needs = False
    if profile.last_onesignal_sync is None:
        needs = True
    elif (now - profile.last_onesignal_sync) > timedelta(days=30):
        needs = True
    request.session['needs_onesignal_sync'] = needs
