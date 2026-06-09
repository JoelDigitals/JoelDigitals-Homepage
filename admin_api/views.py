import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from contact.models import Appointment, AppointmentType, SupportTicket, TicketMessage
from blog.models import BlogPost
from shop_ourapps.models import Order


def _json_error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def _require_auth(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.removeprefix("Bearer ").strip()
    return token == settings.ADMIN_API_SECRET


def _auth_required(view):
    def wrapper(request, *args, **kwargs):
        if not _require_auth(request):
            return _json_error("Unauthorized – gültiger Bearer-Token erforderlich", 401)
        return view(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@_auth_required
def dashboard(request):
    now = timezone.now()
    upcoming = Appointment.objects.filter(
        appointment_datetime__gte=now,
        status="pending",
    ).order_by("appointment_datetime")[:10]

    total_blog_views = BlogPost.objects.aggregate(total=Sum("views"))["total"] or 0

    open_tickets = SupportTicket.objects.filter(is_resolved=False, is_archived=False).count()

    order_status_counts = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    order_counts = {item["status"]: item["count"] for item in order_status_counts}

    return JsonResponse({
        "appointments_upcoming": [
            {
                "id": a.id,
                "name": f"{a.first_name} {a.last_name}",
                "email": a.email,
                "phone": a.phone,
                "type": str(a.appointment_type),
                "datetime": a.appointment_datetime.isoformat(),
                "status": a.status,
            }
            for a in upcoming
        ],
        "blog_views_total": total_blog_views,
        "blog_posts_total": BlogPost.objects.filter(is_published=True).count(),
        "support_open_tickets": open_tickets,
        "order_counts": order_counts,
        "orders_total": Order.objects.count(),
    })


@csrf_exempt
@_auth_required
def appointments(request):
    now = timezone.now()
    pending = Appointment.objects.filter(status="pending", appointment_datetime__gte=now).order_by("appointment_datetime")
    accepted = Appointment.objects.filter(status="accepted", appointment_datetime__gte=now).order_by("appointment_datetime")
    return JsonResponse({
        "pending": [
            {
                "id": a.id,
                "first_name": a.first_name,
                "last_name": a.last_name,
                "email": a.email,
                "phone": a.phone,
                "type": str(a.appointment_type),
                "datetime": a.appointment_datetime.isoformat(),
                "created_at": a.created_at.isoformat(),
            }
            for a in pending
        ],
        "accepted": [
            {
                "id": a.id,
                "first_name": a.first_name,
                "last_name": a.last_name,
                "email": a.email,
                "phone": a.phone,
                "type": str(a.appointment_type),
                "datetime": a.appointment_datetime.isoformat(),
            }
            for a in accepted
        ],
    })


@csrf_exempt
@_auth_required
def appointment_confirm(request, pk):
    from django.core.mail import send_mail

    try:
        appointment = Appointment.objects.get(pk=pk, status="pending")
    except Appointment.DoesNotExist:
        return _json_error("Termin nicht gefunden oder bereits bearbeitet", 404)

    appointment.status = "accepted"
    appointment.save()

    send_mail(
        subject="Termin bestätigt – Joel Digitals",
        message=(
            f"Hallo {appointment.first_name},\n\n"
            f"Ihr Termin am {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} wurde bestätigt.\n\n"
            "Wir freuen uns auf das Gespräch und stehen Ihnen bei Fragen jederzeit zur Verfügung.\n\n"
            f"Details Ihres Termins:\n"
            f"- Terminart: {appointment.appointment_type}\n"
            f"- Datum & Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
            "Bis bald!\nIhr Joel Digitals Team"
        ),
        from_email=settings.COMPANY_EMAIL_NO_REPLY,
        recipient_list=[appointment.email],
    )

    return JsonResponse({"status": "ok", "message": f"Termin {pk} bestätigt"})


@csrf_exempt
@_auth_required
def appointment_reject(request, pk):
    from django.core.mail import send_mail

    try:
        appointment = Appointment.objects.get(pk=pk, status="pending")
    except Appointment.DoesNotExist:
        return _json_error("Termin nicht gefunden oder bereits bearbeitet", 404)

    appointment.status = "rejected"
    appointment.save()

    send_mail(
        subject="Termin abgelehnt – Joel Digitals",
        message=(
            f"Hallo {appointment.first_name},\n\n"
            f"Ihr Termin am {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} wurde leider abgelehnt.\n\n"
            "Bitte buchen Sie ggf. einen neuen Termin über unsere Website.\n\n"
            "Mit freundlichen Grüßen\nIhr Joel Digitals Team"
        ),
        from_email=settings.COMPANY_EMAIL_NO_REPLY,
        recipient_list=[appointment.email],
    )

    return JsonResponse({"status": "ok", "message": f"Termin {pk} abgelehnt"})


@csrf_exempt
@_auth_required
def blog_stats(request):
    total_views = BlogPost.objects.aggregate(total=Sum("views"))["total"] or 0
    posts = BlogPost.objects.filter(is_published=True).order_by("-views")

    return JsonResponse({
        "total_views": total_views,
        "total_posts": BlogPost.objects.count(),
        "published_posts": posts.count(),
        "top_posts": [
            {
                "id": p.id,
                "title_de": p.title_de,
                "views": p.views,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            }
            for p in posts[:20]
        ],
    })


@csrf_exempt
@_auth_required
def support_tickets(request):
    open_tickets = SupportTicket.objects.filter(is_resolved=False, is_archived=False).order_by("-priority", "-created_at")
    resolved_tickets = SupportTicket.objects.filter(is_resolved=True, is_archived=False).order_by("-created_at")[:20]

    return JsonResponse({
        "open": [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "subject": t.subject,
                "name": t.name,
                "email": t.email,
                "priority": t.priority,
                "created_at": t.created_at.isoformat(),
                "message_count": t.messages.count(),
                "assigned_to": str(t.assigned_to) if t.assigned_to else None,
            }
            for t in open_tickets
        ],
        "recently_resolved": [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "subject": t.subject,
                "name": t.name,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in resolved_tickets
        ],
    })


@csrf_exempt
@_auth_required
def support_ticket_detail(request, pk):
    try:
        ticket = SupportTicket.objects.get(pk=pk)
    except SupportTicket.DoesNotExist:
        return _json_error("Ticket nicht gefunden", 404)

    messages = ticket.messages.order_by("created_at")

    return JsonResponse({
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "subject": ticket.subject,
        "description": ticket.description,
        "name": ticket.name,
        "email": ticket.email,
        "priority": ticket.priority,
        "status": "resolved" if ticket.is_resolved else "open",
        "is_archived": ticket.is_archived,
        "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
        "created_at": ticket.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "sender": m.sender.username,
                "message": m.message,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    })


@csrf_exempt
@_auth_required
def support_ticket_reply(request, pk):
    if request.method != "POST":
        return _json_error("Nur POST erlaubt", 405)

    try:
        ticket = SupportTicket.objects.get(pk=pk)
    except SupportTicket.DoesNotExist:
        return _json_error("Ticket nicht gefunden", 404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("Ungültiges JSON", 400)

    message_text = body.get("message", "").strip()
    if not message_text:
        return _json_error("Nachricht darf nicht leer sein", 400)

    from django.contrib.auth.models import User
    jarvis_user, _ = User.objects.get_or_create(
        username="Jarvis",
        defaults={"is_staff": True, "email": "jarvis@joel-digitals.com"},
    )

    msg = TicketMessage.objects.create(
        ticket=ticket,
        sender=jarvis_user,
        message=message_text,
    )

    ticket.is_resolved = False
    ticket.is_archived = False
    ticket.save()

    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives

    ticket_url = f"https://joel-digitals.de/de/contact/support/{ticket.ticket_number}/"
    html_content = render_to_string("emails/ticket_message.html", {
        "ticket": ticket,
        "message": message_text,
        "sender": "Jarvis (API)",
        "ticket_url": ticket_url,
    })
    email = EmailMultiAlternatives(
        subject=f"Neue Nachricht zu Ticket #{ticket.ticket_number}",
        body=f"Es gibt eine neue Antwort zu Ihrem Ticket.\n\n{ticket_url}\n\n{message_text}",
        from_email=settings.COMPANY_EMAIL_NO_REPLY,
        to=[ticket.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    return JsonResponse({
        "status": "ok",
        "message_id": msg.id,
        "created_at": msg.created_at.isoformat(),
        "sender": "Jarvis",
    })


@csrf_exempt
@_auth_required
def support_ticket_resolve(request, pk):
    if request.method != "POST":
        return _json_error("Nur POST erlaubt", 405)

    try:
        ticket = SupportTicket.objects.get(pk=pk)
    except SupportTicket.DoesNotExist:
        return _json_error("Ticket nicht gefunden", 404)

    ticket.is_resolved = not ticket.is_resolved
    if ticket.is_resolved:
        ticket.resolved_at = timezone.now()
    else:
        ticket.resolved_at = None
    ticket.save()

    return JsonResponse({
        "status": "ok",
        "ticket_id": ticket.id,
        "is_resolved": ticket.is_resolved,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    })


@csrf_exempt
@_auth_required
def orders(request):
    status_counts = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    recent = Order.objects.order_by("-created_at")[:20]

    return JsonResponse({
        "status_counts": {item["status"]: item["count"] for item in status_counts},
        "total": Order.objects.count(),
        "recent_orders": [
            {
                "id": o.id,
                "first_name": o.first_name,
                "last_name": o.last_name,
                "email": o.email,
                "status": o.status,
                "total_amount": str(o.total_amount),
                "payment_method": o.payment_method,
                "created_at": o.created_at.isoformat(),
                "item_count": o.items.count(),
            }
            for o in recent
        ],
    })
