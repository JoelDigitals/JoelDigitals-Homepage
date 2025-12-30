from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from .forms import ContactForm, SalesWishForm, SupportTicketForm, TicketMessageForm, AppointmentForm
from django.contrib import messages
from django.http import HttpResponse
from .models import SalesWish, SupportTicket, TicketMessage, SalesChatMessage, SalesEntry, TicketNote, Appointment, AppointmentType, TimeSlot, SpecialTimeSlot
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta, datetime
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from contact.utils import get_available_times, is_slot_available
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import make_aware
from django.http import JsonResponse


def generate_time_slots(start_dt, end_dt, slot_interval_minutes=10):
    """
    Generiert Zeitslots im definierten Intervall (z.B. alle 10 Minuten).
    Diese sind die STARTZEITEN für mögliche Termine.
    """
    slots = []
    current = start_dt
    
    while current < end_dt:
        slots.append(current)
        current += timedelta(minutes=slot_interval_minutes)
    
    return slots

def is_slot_available(slot_start, duration_minutes, max_parallel=2):
    """
    Prüft, ob zu einem bestimmten Startzeitpunkt noch Kapazität frei ist.
    Ein Termin blockiert die Zeit von slot_start bis slot_start + duration_minutes.
    
    Berücksichtigt Überschneidungen mit bestehenden Terminen unterschiedlicher Dauer.
    """
    slot_start_aware = make_aware(slot_start) if slot_start.tzinfo is None else slot_start
    slot_end = slot_start_aware + timedelta(minutes=duration_minutes)
    
    # Zähle alle Termine, die sich mit diesem Zeitfenster überschneiden
    # Ein bestehender Termin überschneidet sich, wenn:
    # - er vor unserem Ende beginnt UND
    # - er nach unserem Start endet (unter Berücksichtigung seiner eigenen Dauer)
    
    overlapping_appointments = Appointment.objects.filter(
        appointment_datetime__lt=slot_end,  # Beginnt vor unserem Ende
        status__in=['pending', 'accepted']  # Nur aktive Termine
    ).exclude(
        status='rejected'
    )
    
    # Prüfe für jeden Termin, ob er wirklich überschneidet
    overlapping_count = 0
    for appt in overlapping_appointments:
        appt_end = appt.appointment_datetime + timedelta(minutes=appt.appointment_type.duration_minutes)
        # Wenn der Termin nach unserem Start endet, gibt es eine Überschneidung
        if appt_end > slot_start_aware:
            overlapping_count += 1
    
    return overlapping_count < max_parallel

def get_available_times(selected_date, appointment_type, max_parallel=2):
    """
    Gibt alle verfügbaren Zeitslots für ein bestimmtes Datum zurück.
    Slots starten alle 5 Minuten, jeder Termin blockiert die Dauer seines Termintyps.
    
    Args:
        selected_date: Das Datum für das Slots gesucht werden
        appointment_type: Der AppointmentType mit duration_minutes Attribut
        max_parallel: Maximale Anzahl paralleler Termine (Standard: 2)
    """
    duration_minutes = appointment_type.duration_minutes
    slot_interval = 10  # Startzeiten alle 5 Minuten
    
    all_possible_slots = []
    
    # 1. Reguläre TimeSlots für den Wochentag
    regular_slots = TimeSlot.objects.filter(weekday=selected_date.weekday())
    for ts in regular_slots:
        start_dt = datetime.combine(selected_date, ts.start_time)
        end_dt = datetime.combine(selected_date, ts.end_time)
        
        # Stelle sicher, dass der letzte mögliche Termin noch vollständig in die Zeitspanne passt
        # Reduziere end_dt um die Termindauer
        effective_end = end_dt - timedelta(minutes=duration_minutes)
        
        if effective_end > start_dt:
            all_possible_slots += generate_time_slots(start_dt, effective_end + timedelta(minutes=slot_interval), slot_interval)
    
    # 2. Spezielle TimeSlots für dieses Datum
    special_slots = SpecialTimeSlot.objects.filter(date=selected_date)
    for sts in special_slots:
        start_dt = datetime.combine(selected_date, sts.start_time)
        end_dt = datetime.combine(selected_date, sts.end_time)
        
        # Auch hier: letzter Termin muss vollständig passen
        effective_end = end_dt - timedelta(minutes=duration_minutes)
        
        if effective_end > start_dt:
            all_possible_slots += generate_time_slots(start_dt, effective_end + timedelta(minutes=slot_interval), slot_interval)
    
    # 3. Duplikate entfernen und sortieren
    all_possible_slots = sorted(set(all_possible_slots))
    
    # 4. Verfügbarkeit prüfen
    available_slots = []
    current_time = now()
    
    for slot_dt in all_possible_slots:
        slot_aware = make_aware(slot_dt) if slot_dt.tzinfo is None else slot_dt
        
        # Überspringe vergangene Zeitslots
        if slot_aware <= current_time:
            continue
        
        # Prüfe Verfügbarkeit mit der korrekten Dauer
        is_available = is_slot_available(slot_dt, duration_minutes, max_parallel)
        
        available_slots.append({
            "datetime": slot_aware,
            "time": slot_aware.strftime("%H:%M"),
            "full": not is_available
        })
    
    return available_slots

def get_available_dates(request):
    """API-Endpoint: Liefert verfügbare Daten für die nächsten 60 Tage"""
    dates = []
    today = datetime.today().date()
    
    for i in range(2, 100):
        d = today + timedelta(days=i)
        # Optional: Prüfe, ob an diesem Tag überhaupt Slots existieren
        has_regular = TimeSlot.objects.filter(weekday=d.weekday()).exists()
        has_special = SpecialTimeSlot.objects.filter(date=d).exists()
        
        if has_regular or has_special:
            dates.append(d.strftime("%Y-%m-%d"))
    
    return JsonResponse({"dates": dates})

def get_slots(request):
    """API-Endpoint: Liefert verfügbare Zeitslots für ein bestimmtes Datum"""
    date_str = request.GET.get("date")
    type_id = request.GET.get("type")
    
    if not date_str or not type_id:
        return JsonResponse({"slots": [], "error": "Datum und Termintyp erforderlich"})
    
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appointment_type = AppointmentType.objects.get(id=type_id)
    except (ValueError, AppointmentType.DoesNotExist):
        return JsonResponse({"slots": [], "error": "Ungültiges Datum oder Termintyp"})
    
    slots = get_available_times(selected_date, appointment_type)
    
    # JSON-Ausgabe vorbereiten
    slots_list = [
        {
            "datetime": s["datetime"].isoformat(),
            "time": s["time"],
            "full": s["full"]
        }
        for s in slots
    ]
    
    return JsonResponse({"slots": slots_list})

def appointment_create(request):
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
                
                return redirect("appointment_success")
    else:
        form = AppointmentForm()
    
    return render(request, "contact/appointment_form.html", {
        "form": form,
    })

def appointment_success(request):
    """Erfolgsseite nach Terminbuchung"""
    return render(request, "contact/appointment_success.html")


@login_required
def appointment_admin_view(request):
    pending = Appointment.objects.filter(status='pending').order_by('appointment_datetime')
    accepted = Appointment.objects.filter(status='accepted').order_by('appointment_datetime')
    rejected = Appointment.objects.filter(status='rejected').order_by('appointment_datetime')
    return render(request, 'contact/termin_admin.html', {
        'pending': pending,
        'accepted': accepted,
        'rejected': rejected,
    })


@login_required
def update_appointment_status(request, pk, status):
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
        return redirect('appointment_admin')  # keine Mail bei pending

    send_mail(
        subject=subject,
        message=message,
        from_email='support@joel-digitals.com',
        recipient_list=[appointment.email],
    )

    return redirect('appointment_admin')

def appointment_success(request):
    return render(request, 'contact/appointment_success.html')

def is_Support_Ticket_Admin(user):
    return user.groups.filter(name='Admin Support').exists()

def is_Sales_Editor(user):
    return user.groups.filter(name='Selling').exists()

def is_Support_Editor(user):
    return user.groups.filter(name='Support').exists()

def index(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'contact/index.html', {'user_groups': user_groups})

def contact_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        name = form.cleaned_data['name']
        message = form.cleaned_data['message']

        send_mail(
            subject=f"Kontaktanfrage von {name}, Email: {form.cleaned_data['email']}",
            message=message,
            from_email='support@joel-digitals.com',
            recipient_list=['info@joel-digitals.com'],
        )

        messages.success(request, "Deine Nachricht wurde erfolgreich gesendet.")
        return redirect('contact_form')

    return render(request, 'contact/contact.html', {'form': form, 'user_groups': user_groups})

@login_required
def sales(request):
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

    return render(request, 'contact/sales.html', {
        'entries': entries,
        'user_groups': user_groups
    })

@login_required
def sales_chat(request, entry_id):
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

    return render(request, 'contact/sales_chat.html', {
        'entry': entry,
        'messages': messages_qs,
        'user_groups': user_groups
    })

@login_required
def send_chat_message(request, entry_id):
    entry = get_object_or_404(SalesEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        message = request.POST.get('chat_message')
        if message.strip():
            SalesChatMessage.objects.create(entry=entry, user=request.user, message=message)
    return redirect('sales')

@login_required
def export_wishes(request):
    wishes = SalesWish.objects.all()
    content = "\n\n".join([f"{w.name} ({w.email}):\n{w.wishes}" for w in wishes])
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=wunschliste.txt'
    return response

@login_required
def support_tickets(request):
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
        return redirect('support_tickets')

    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')  # hier auch "user"
    return render(request, 'contact/support.html', {'form': form, 'tickets': tickets, 'user_groups': user_groups})

@login_required
def ticket_detail(request, ticket_number):
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
def admin_ticket_view(request):
    user = request.user
    is_editor = is_Support_Editor(user)
    is_admin = is_Support_Ticket_Admin(user)

    if not (is_editor or is_admin):
        return redirect("support_tickets")

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

            return redirect("admin_tickets")


    return render(request, "contact/admin_tickets.html", {
        "tickets": tickets,
        "is_admin": is_admin,
        "user_groups": [g.name for g in user.groups.all()],
        "support_users": support_users,
    })

@user_passes_test(is_Sales_Editor)
def admin_sales_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    entries = SalesEntry.objects.all().order_by('-created_at')
    return render(request, 'contact/admin_sales.html', {'entries': entries, 'user_groups': user_groups})

def sales_entry_detail(request, entry_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    entry = get_object_or_404(SalesEntry, id=entry_id)
    wishes = entry.wishes.all()
    return render(request, 'contact/sales_entry_detail.html', {'entry': entry, 'wishes': wishes, 'user_groups': user_groups})

def add_wish(request, entry_id):
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
            
            return redirect('sales_entry_detail', entry_id=entry_id)
    else:
        form = SalesWishForm()

    return render(request, 'contact/wish_form.html', {'form': form, 'title': 'Neuen Wunsch hinzufügen', 'user_groups': user_groups})

def edit_wish(request, entry_id, wish_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    wish = get_object_or_404(SalesWish, pk=wish_id)
    if request.method == 'POST':
        form = SalesWishForm(request.POST, instance=wish)
        if form.is_valid():
            form.save()
            return redirect('sales_entry_detail', entry_id=entry_id)
    else:
        form = SalesWishForm(instance=wish)
    return render(request, 'contact/wish_form.html', {'form': form, 'title': 'Wunsch bearbeiten', 'user_groups': user_groups})

def delete_wish(request, entry_id, wish_id):
    wish = get_object_or_404(SalesWish, pk=wish_id)
    if request.method == 'POST':
        wish.delete()
        return redirect('sales_entry_detail', entry_id=entry_id)
    return render(request, 'contact/confirm_delete.html', {'wish': wish})

def export_single_wish(request, entry_id, wish_id):
    wish = get_object_or_404(SalesWish, pk=wish_id)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=wunsch_{wish.id}.txt'
    response.write(f'Name: {wish.name}\n')
    response.write(f'Email: {wish.email}\n')
    response.write(f'Wunsch: {wish.wishes}\n')
    response.write(f'Erstellt am: {wish.created_at}\n')
    return response

@login_required
def ticket_archive_view(request):
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

    return render(request, 'contact/ticket_archive.html', {
        'page_obj': page_obj,
        'query': query,
        'user_groups': [g.name for g in request.user.groups.all()],
    })

def auto_archive_tickets():
    for ticket in SupportTicket.objects.filter(is_resolved=True, is_archived=False):
        ticket.check_and_archive()

@login_required
def ticket_detail_view(request, ticket_number):
    if not (is_Support_Ticket_Admin(request.user) or is_Support_Editor(request.user)):
        raise PermissionDenied()

    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number, is_archived=True)

    return render(request, 'contact/archive_ticket_detail.html', {
        'ticket': ticket,
        'user_groups': [g.name for g in request.user.groups.all()],
    })
