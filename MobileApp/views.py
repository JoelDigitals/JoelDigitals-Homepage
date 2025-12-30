from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from contact.forms import ContactForm, SalesWishForm, SupportTicketForm, TicketMessageForm, AppointmentForm
from django.contrib import messages
from django.http import HttpResponse
from contact.models import SalesWish, SupportTicket, TicketMessage, SalesChatMessage, SalesEntry, TicketNote, Appointment
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta, datetime
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from contact.views import is_Sales_Editor, is_Support_Ticket_Admin, is_Support_Editor
from contact.utils import get_available_times, is_slot_available
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse


def login_view_app(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home_app')  # oder eine andere Zielseite
    else:
        form = AuthenticationForm()
    return render(request, 'mobile/login.html', {'form': form, 'user_groups': user_groups})

from django.shortcuts import redirect

def logout_view_app(request):
    logout(request)
    return redirect('home_app')  # KEINE weiteren Argumente hier

def home_view_app(request):
    user = request.user
    groups = user.groups.values_list('name', flat=True)

    context = {
        'user': user,
        'is_superuser': user.is_superuser,
        'in_support_sales': 'Selling' in groups,
        'in_support_tickets': 'Support' in groups,
        'in_support_admin': 'support_admAdmin Supportin' in groups,
        'in_marketing' : 'Marketing' in groups,
        'user_groups': list(groups),
    }
    return render(request, 'mobile/home.html', context)



@login_required
def sales_app(request):
    user_groups = [group.name for group in request.user.groups.all()]

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        entry = SalesEntry.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user=request.user
        )

        index = 0
        while True:
            title = request.POST.get(f"wishes[{index}][title]")
            description = request.POST.get(f"wishes[{index}][description]")
            if title and description:
                SalesWish.objects.create(entry=entry, title=title, description=description)
                index += 1
            else:
                break

        # 📧 HTML-Mail beim Erstellen
        html_content = render_to_string(
            "emails/sales_entry_created.html",
            {"entry": entry}
        )

        email_msg = EmailMultiAlternatives(
            subject=f"Neue Sales-Anfrage: {entry.subject}",
            body="Neue Sales-Anfrage",
            from_email=settings.COMPANY_EMAIL_NO_REPLY,
            to=["info@joel-digitals.com"]
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        messages.success(request, "Wünsche wurden gespeichert.")
        return redirect('sales')

    entries = SalesEntry.objects.filter(user=request.user)\
        .prefetch_related('wishes', 'chat_messages')\
        .order_by('-created_at')

    return render(request, 'mobile/sales.html', {
        'entries': entries,
        'user_groups': user_groups
    })

@login_required
def sales_chat_app(request, entry_id):
    user_groups = [group.name for group in request.user.groups.all()]
    entry = get_object_or_404(SalesEntry, id=entry_id)

    if request.user != entry.user and not request.user.is_staff:
        raise PermissionDenied()

    if request.method == "POST":
        message_text = request.POST.get("message")

        if message_text:
            SalesChatMessage.objects.create(
                entry=entry,
                user=request.user,
                message=message_text
            )

            # 🔁 Empfänger bestimmen
            if request.user == entry.user:
                recipient = "info@joel-digitals.com"
            else:
                recipient = entry.email

            chat_url = request.build_absolute_uri(
                reverse("sales_chat", args=[entry.id])
            )

            html_content = render_to_string(
                "emails/sales_chat_message.html",
                {
                    "entry": entry,
                    "message": message_text,
                    "sender": request.user.get_full_name() or request.user.username,
                    "chat_url": chat_url
                }
            )

            email_msg = EmailMultiAlternatives(
                subject=f"Neue Nachricht: {entry.subject}",
                body="Neue Chat-Nachricht",
                from_email=settings.COMPANY_EMAIL_NO_REPLY,
                to=[recipient]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()

            return redirect('sales_chat', entry_id=entry.id)

    messages_qs = SalesChatMessage.objects.filter(entry=entry).order_by('created_at')

    return render(request, 'mobile/sales_chat.html', {
        'entry': entry,
        'messages': messages_qs,
        'user_groups': user_groups
    })

@login_required
def send_chat_message_app(request, entry_id):
    entry = get_object_or_404(SalesEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        message = request.POST.get('chat_message')
        if message.strip():
            SalesChatMessage.objects.create(entry=entry, user=request.user, message=message)
    return redirect('sales_app')

@login_required
def export_wishes_app(request):
    wishes = SalesWish.objects.all()
    content = "\n\n".join([f"{w.name} ({w.email}):\n{w.wishes}" for w in wishes])
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=wunschliste.txt'
    return response

@login_required
def support_tickets_app(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    form = SupportTicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = request.user  # korrektes Feld ist "user"
        ticket.save()
        # Erste Nachricht automatisch erzeugen
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=ticket.description
        )
        send_mail(
            subject=f"Neues Support-Ticket: {ticket.subject}",
            message=f"Ein neues Support-Ticket wurde erstellt.\n\nTicket-Nummer: {ticket.ticket_number}\nBetreff: {ticket.subject}\n\nBitte im Admin-Bereich prüfen.",
            from_email=settings.COMPANY_EMAIL_NO_REPLY,
            recipient_list=[settings.SUPPORT_EMAIL]
        )
        send_mail(
            subject=f"Dein Support-Ticket wurde erstellt: {ticket.subject}",
            message=f"Hallo {request.user.get_full_name() or request.user.username},\n\n"
                    f"dein Support-Ticket wurde erfolgreich erstellt.\n\n"
                    f"Ticket-Nummer: {ticket.ticket_number}\n"
                    f"Betreff: {ticket.subject}\n\n"
                    "Unser Support-Team wird sich so schnell wie möglich bei dir melden.\n\n"
                    "Vielen Dank für deine Geduld!\n\n"
                    "Mit freundlichen Grüßen\n"
                    "Dein Joel Digitals Team",
            from_email=settings.COMPANY_EMAIL_NO_REPLY,
            recipient_list=[ticket.email]
        )
        messages.success(request, "Ticket erfolgreich erstellt.")
        return redirect('support_tickets_app')

    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')  # hier auch "user"
    return render(request, 'mobile/support.html', {'form': form, 'tickets': tickets, 'user_groups': user_groups})

@login_required
def ticket_detail_app(request, ticket_number):
    user_groups = [group.name for group in request.user.groups.all()]
    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number)

    # 🔐 Zugriff prüfen
    if ticket.user != request.user and not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender = request.user
            message.save()

            # 🔁 Ticket ggf. reaktivieren
            ticket.reactivate_if_new_message(request.user)

            # 🔁 Empfänger bestimmen
            if request.user == ticket.user:
                recipient = settings.SUPPORT_EMAIL  # z. B. info@joel-digitals.com
            else:
                recipient = ticket.user.email

            ticket_url = request.build_absolute_uri(
                reverse("ticket_detail", args=[ticket.ticket_number])
            )

            html_content = render_to_string(
                "emails/ticket_message.html",
                {
                    "ticket": ticket,
                    "message": message.message,
                    "sender": request.user.get_full_name() or request.user.username,
                    "ticket_url": ticket_url
                }
            )

            email = EmailMultiAlternatives(
                subject=f"Neue Nachricht zu Ticket #{ticket.ticket_number}",
                body="Neue Ticket-Nachricht",
                from_email=settings.COMPANY_EMAIL_NO_REPLY,
                to=[recipient]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            messages.success(request, "Nachricht gesendet.")
            return redirect('ticket_detail', ticket_number=ticket.ticket_number)

    else:
        form = TicketMessageForm()

    messages_list = ticket.messages.order_by('created_at')

    return render(request, 'contact/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages_list,
        'form': form,
        'user_groups': user_groups
    })

@login_required
def admin_ticket_view_app(request):
    user = request.user
    is_editor = is_Support_Editor(user)
    is_admin = is_Support_Ticket_Admin(user)

    if not (is_editor or is_admin):
        return redirect("support_tickets_app")

    if is_admin:
        tickets = SupportTicket.objects.filter(is_archived=False).order_by('-priority')
        support_users_raw = User.objects.filter(groups__name__in=["Support", "Admin Support"]).distinct()
        support_users = [u for u in support_users_raw if is_Support_Editor(u) or is_Support_Ticket_Admin(u)]
    else:
        tickets = SupportTicket.objects.filter(is_archived=False, assigned_to=user).order_by('-priority')
        support_users = []

    for ticket in tickets:
        ticket.check_auto_archive()

    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        action = request.POST.get("action")

        if request.method == "POST":
            ticket_id = request.POST.get("ticket_id")
            action = request.POST.get("action")

            if ticket_id:
                ticket = get_object_or_404(SupportTicket, id=ticket_id)

                # Jeder Supporter darf Status toggeln
                if action == "toggle" and (is_admin or is_editor):
                    ticket.is_resolved = not ticket.is_resolved
                    if ticket.is_resolved:
                        ticket.resolved_at = timezone.now()
                    else:
                        ticket.resolved_at = None
                    ticket.save()

                # Admin-Only: assigned_to und priority ändern
                if is_admin:
                    changed = False
                    assigned_id = request.POST.get("assigned_to")
                    if assigned_id:
                        try:
                            assigned_user = User.objects.get(id=assigned_id)
                            if is_Support_Editor(assigned_user) or is_Support_Ticket_Admin(assigned_user):
                                if ticket.assigned_to != assigned_user:
                                    ticket.assigned_to = assigned_user
                                    changed = True
                        except User.DoesNotExist:
                            pass
                        
                    priority = request.POST.get("priority")
                    if priority in dict(SupportTicket.PRIORITY_CHOICES):
                        if ticket.priority != priority:
                            ticket.priority = priority
                            changed = True

                    if changed:
                        ticket.save()

                # Notiz speichern für alle Supporter (Editoren & Admins)
                if is_editor or is_admin:
                    note_text = request.POST.get("note")
                    if note_text:
                        TicketNote.objects.create(ticket=ticket, author=user, note=note_text)

            return redirect("admin_tickets_app")


    return render(request, "mobile/admin_tickets.html", {
        "tickets": tickets,
        "is_admin": is_admin,
        "user_groups": [g.name for g in user.groups.all()],
        "support_users": support_users,
    })

@user_passes_test(is_Sales_Editor)
def admin_sales_view_app(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    entries = SalesEntry.objects.all().order_by('-created_at')
    return render(request, 'mobile/admin_sales.html', {'entries': entries, 'user_groups': user_groups})

def sales_entry_detail_app(request, entry_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    entry = get_object_or_404(SalesEntry, id=entry_id)
    wishes = entry.wishes.all()
    return render(request, 'mobile/sales_entry_detail.html', {'entry': entry, 'wishes': wishes, 'user_groups': user_groups})

def add_wish_app(request, entry_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    # Holen des Entry-Objekts, das dem Wunsch zugeordnet werden soll
    entry = get_object_or_404(SalesEntry, id=entry_id)
    
    if request.method == 'POST':
        form = SalesWishForm(request.POST)
        if form.is_valid():
            # Speichern des neuen Wunsches und Zuweisen des entry
            wish = form.save(commit=False)  # Nur speichern, ohne direkt in der DB zu committen
            wish.entry = entry  # Setze die entry-Referenz
            wish.save()  # Jetzt speichern
            
            return redirect('sales_entry_detail_app', entry_id=entry_id)
    else:
        form = SalesWishForm()

    return render(request, 'mobile/wish_form.html', {'form': form, 'title': 'Neuen Wunsch hinzufügen', 'user_groups': user_groups})

def edit_wish_app(request, entry_id, wish_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    wish = get_object_or_404(SalesWish, pk=wish_id)
    if request.method == 'POST':
        form = SalesWishForm(request.POST, instance=wish)
        if form.is_valid():
            form.save()
            return redirect('sales_entry_detail_app', entry_id=entry_id)
    else:
        form = SalesWishForm(instance=wish)
    return render(request, 'mobile/wish_form.html', {'form': form, 'title': 'Wunsch bearbeiten', 'user_groups': user_groups})

def delete_wish_app(request, entry_id, wish_id):
    wish = get_object_or_404(SalesWish, pk=wish_id)
    if request.method == 'POST':
        wish.delete()
        return redirect('sales_entry_detail_app', entry_id=entry_id)
    return render(request, 'mobile/confirm_delete.html', {'wish': wish})

def export_single_wish_app(request, entry_id, wish_id):
    wish = get_object_or_404(SalesWish, pk=wish_id)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=wunsch_{wish.id}.txt'
    response.write(f'Name: {wish.name}\n')
    response.write(f'Email: {wish.email}\n')
    response.write(f'Wunsch: {wish.wishes}\n')
    response.write(f'Erstellt am: {wish.created_at}\n')
    return response

@login_required
def ticket_archive_view_app(request):
    if not (is_Support_Ticket_Admin(request.user) or is_Support_Editor(request.user)):
        raise PermissionDenied()

    query = request.GET.get('q', '')
    tickets = SupportTicket.objects.filter(is_archived=True)

    if query:
        tickets = tickets.filter(
            Q(user__email__icontains=query) |
            Q(ticket_number__icontains=query) |
            Q(subject__icontains=query) |
            Q(resolved_at__isnull=False) |  # Nur Tickets, die gelöst wurden
            Q(resolved_at__icontains=query)
        )


    paginator = Paginator(tickets.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'mobile/ticket_archive.html', {
        'page_obj': page_obj,
        'query': query,
        'user_groups': [g.name for g in request.user.groups.all()],
    })

def auto_archive_tickets_app():
    for ticket in SupportTicket.objects.filter(is_resolved=True, is_archived=False):
        ticket.check_and_archive()

@login_required
def ticket_detail_view_app(request, ticket_number):
    if not (is_Support_Ticket_Admin(request.user) or is_Support_Editor(request.user)):
        raise PermissionDenied()

    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number, is_archived=True)

    return render(request, 'mobile/archive_ticket_detail.html', {
        'ticket': ticket,
        'user_groups': [g.name for g in request.user.groups.all()],
    })

def appointment_create_app(request):
    """Hauptview für die Terminbuchung"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment_type = appointment.appointment_type
            
            # Finale Verfügbarkeitsprüfung
            slot_start = appointment.appointment_datetime
            
            if not is_slot_available(
                slot_start, 
                appointment_type.duration_minutes, 
                max_parallel=2
            ):
                form.add_error(
                    "appointment_datetime", 
                    "Dieser Zeitslot ist leider bereits ausgebucht. Bitte wählen Sie einen anderen."
                )
            else:
                appointment.save()
                
                # E-Mail-Benachrichtigung
                send_mail(
                    subject=f"Neue Terminbuchung: {appointment_type.name}",
                    message=f"""
Neuer Termin wurde gebucht:

Name: {appointment.first_name} {appointment.last_name}
E-Mail: {appointment.email}
Telefon: {appointment.phone}
Terminart: {appointment_type.name}
Datum/Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}
Dauer: {appointment_type.duration_minutes} Minuten

Status: {appointment.get_status_display()}
                    """,
                    from_email="no-reply@joel-digitals.com",
                    recipient_list=["info@joel-digitals.com"],
                    fail_silently=False,
                )
                
                return redirect("appointment_success_app")
    else:
        form = AppointmentForm()

    return render(request, "mobile/appointment_form.html", {
        "form": form
    })


def appointment_success_app(request):
    return render(request, "mobile/appointment_success.html")


@login_required
def appointment_admin_view_app(request):
    pending = Appointment.objects.filter(status='pending').order_by('appointment_datetime')
    accepted = Appointment.objects.filter(status='accepted').order_by('appointment_datetime')
    rejected = Appointment.objects.filter(status='rejected').order_by('appointment_datetime')
    return render(request, 'mobile/termin_admin.html', {
        'pending': pending,
        'accepted': accepted,
        'rejected': rejected,
    })


@login_required
def update_appointment_status_app(request, pk, status):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = status
    appointment.save()

    # Automatische E-Mail
    if status == 'accepted':
        subject = "Termin bestätigt – Joel Digitals"
        message = (
            f"Hallo {appointment.first_name},\n\n"
            f"Ihr Termin am {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} wurde bestätigt.\n\n"
            "Wir freuen uns auf das Gespräch und stehen Ihnen bei Fragen jederzeit zur Verfügung.\n\n"
            "Bitte beachten Sie, dass Sie den Termin bis zu 24 Stunden vorher absagen können.\n\n"
            f"Details Ihres Termins:\n"
            f"- Terminart: {appointment.appointment_type}\n"
            f"- Datum & Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"

            "Bitte halten Sie sich den Termin frei und seien Sie pünktlich.\n\n" \
            f"Bitte rufen sie und am {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} an unter der Nummer: +4915253480270 an\n\n"
            "Mit freundlichen Grüßen\n"
            "Bis bald!\nIhr Joel Digitals Team"
        )
    elif status == 'rejected':
        subject = "Termin abgelehnt – Joel Digitals"
        message = (
            f"Hallo {appointment.first_name},\n\n"
            f"Ihr Termin am {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')} wurde leider abgelehnt.\n\n"
            "Bitte buchen Sie ggf. einen neuen Termin.\n\n"
            "Wir entschuldigen uns für die Unannehmlichkeiten und hoffen, dass wir bald einen passenden Termin finden.\n\n"
            "Bitte buchen Sie ggf. einen neuen Termin über unsere Website oder nehmen sie über unser Kontaktformular/Ticketsystem Kontakt mit uns auf.\n\n"
            
            "Hier sind wir erreichbar:\n"
            "https://joel-digitals.de/contact/\n\n"
            "Telefon: +4915253480270\n\n"
            "E-Mail: info@joel-digitals.com\n\n"

            "Details Ihres Termins:\n"
            f"- Terminart: {appointment.appointment_type}\n"
            f"- Datum & Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
            "Bitte zögern Sie nicht, uns bei Fragen zu kontaktieren.\n\n"
            "Wir danken Ihnen für Ihr Verständnis und Ihre Geduld.\n\n"

            "Mit freundlichen Grüßen\n"
            "Ihr Joel Digitals Team"
        )
    else:
        return redirect('appointment_admin_app')  # keine Mail bei pending

    send_mail(
        subject=subject,
        message=message,
        from_email='no-reply@joel-digitals.com',
        recipient_list=[appointment.email],
    )

    return redirect('appointment_admin')

