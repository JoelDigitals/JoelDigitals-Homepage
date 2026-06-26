from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Webinar, WebinarRegistration


def webinar_list(request):
    now = timezone.now()
    upcoming = Webinar.objects.filter(
        is_active=True,
        date_time__gte=now,
    ).filter(
        Q(registration_start__isnull=True) | Q(registration_start__lte=now)
    ).order_by('date_time')

    past = Webinar.objects.filter(
        is_active=True,
        date_time__lt=timezone.now()
    ).order_by('-date_time')[:6]

    return render(request, 'webinars/webinar_list.html', {
        'upcoming_webinars': upcoming,
        'past_webinars': past,
        'now': timezone.now(),
    })


def webinar_detail(request, slug):
    webinar = get_object_or_404(Webinar, slug=slug, is_active=True)
    user_registration = None
    is_full = webinar.is_full

    if request.user.is_authenticated:
        user_registration = WebinarRegistration.objects.filter(
            webinar=webinar, user=request.user
        ).first()

    return render(request, 'webinars/webinar_detail.html', {
        'webinar': webinar,
        'user_registration': user_registration,
        'is_full': is_full,
        'now': timezone.now(),
    })


@login_required
def webinar_register(request, slug):
    webinar = get_object_or_404(Webinar, slug=slug, is_active=True)

    if request.method == 'POST':
        if not webinar.is_registration_open:
            if webinar.is_past:
                messages.error(request, _("Dieses Webinar hat bereits stattgefunden."))
            elif webinar.registration_start and webinar.registration_start > timezone.now():
                messages.error(request, _("Die Anmeldung für dieses Webinar hat noch nicht begonnen."))
            else:
                messages.error(request, _("Der Anmeldezeitraum für dieses Webinar ist vorbei."))
            return redirect('webinars:webinar_detail', slug=slug)

        existing = WebinarRegistration.objects.filter(
            webinar=webinar, user=request.user
        ).first()

        if existing:
            if existing.status == 'cancelled':
                existing.status = 'registered'
                existing.save()
                messages.success(request, _("Deine Anmeldung wurde reaktiviert."))
            else:
                messages.info(request, _("Du bist bereits für dieses Webinar angemeldet."))
        elif webinar.is_full:
            messages.error(request, _("Dieses Webinar ist bereits ausgebucht."))
        else:
            WebinarRegistration.objects.create(
                webinar=webinar,
                user=request.user,
            )
            messages.success(request, _("Du wurde erfolgreich für das Webinar angemeldet!"))

            # Bestätigungsmail senden (HTML)
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                ctx = {
                    'user': request.user,
                    'webinar': webinar,
                }
                html = render_to_string('emails/webinar_confirmation.html', ctx)
                msg = EmailMultiAlternatives(
                    subject=f"Anmeldung bestätigt: {webinar.title}",
                    body=f"Hallo {request.user.first_name or request.user.username},\n\ndeine Anmeldung für '{webinar.title}' ist eingegangen.\n\nTermin: {webinar.date_time.strftime('%d.%m.%Y um %H:%M')} Uhr\nDauer: ca. {webinar.duration_minutes} Minuten\n\nDer Zugangslink wird dir rechtzeitig vor dem Webinar per E-Mail zugesandt.\n\nViele Grüße,\nDein Joel Digitals Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[request.user.email],
                )
                msg.attach_alternative(html, "text/html")
                msg.send()
            except Exception:
                pass

        return redirect('webinars:webinar_detail', slug=slug)

    return redirect('webinars:webinar_detail', slug=slug)


@login_required
def webinar_cancel(request, slug):
    webinar = get_object_or_404(Webinar, slug=slug, is_active=True)

    if request.method == 'POST':
        registration = WebinarRegistration.objects.filter(
            webinar=webinar, user=request.user, status='registered'
        ).first()

        if registration:
            registration.status = 'cancelled'
            registration.save()
            messages.success(request, _("Deine Anmeldung wurde storniert."))
        else:
            messages.info(request, _("Keine aktive Anmeldung gefunden."))

    return redirect('webinars:webinar_detail', slug=slug)
