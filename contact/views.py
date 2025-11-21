from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from .forms import ContactForm, SalesWishForm, SupportTicketForm, TicketMessageForm, AppointmentForm
from django.contrib import messages
from django.http import HttpResponse
from .models import SalesWish, SupportTicket, TicketMessage, SalesChatMessage, SalesEntry, TicketNote, Appointment
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()

            # Mail an uns (intern)
            admin_subject = f"Neue Terminbuchung von {appointment.first_name} {appointment.last_name}"
            admin_message = (
                f"Neue Terminbuchung:\n\n"
                f"Name: {appointment.first_name} {appointment.last_name}\n"
                f"E-Mail: {appointment.email}\n"
                f"Telefon: {appointment.phone}\n"
                f"Terminart: {appointment.appointment_type}\n"
                f"Datum & Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            )

            send_mail(
                subject=admin_subject,
                message=admin_message,
                from_email='-support@joel-digitals.com',
                recipient_list=['info@joel-digitals.com'],
            )

            # Mail an Kunden (Bestätigung)
            client_subject = "Ihre Terminbuchung bei Joel Digitals"
            client_message = (
                f"Hallo {appointment.first_name},\n\n"
                "vielen Dank für Ihre Terminbuchung bei Joel Digitals. Wir haben Ihre Anfrage erhalten und werden sie bald prüfen.\n\n"
                f"Details Ihres Termins:\n"
                f"- Terminart: {appointment.appointment_type}\n"
                f"- Datum & Uhrzeit: {appointment.appointment_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                "Sie erhalten eine weitere E-Mail, sobald wir den Termin bestätigen oder ablehnen.\n\n"
                "Mit freundlichen Grüßen\n"
                "Ihr Joel Digitals Team"
            )

            send_mail(
                subject=client_subject,
                message=client_message,
                from_email='support@joel-digitals.com',
                recipient_list=[appointment.email],
            )

            return redirect('appointment_success')
    else:
        form = AppointmentForm()

    return render(request, 'contact/appointment_form.html', {'form': form})


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
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
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

        messages.success(request, "Wünsche wurden gespeichert.")
        return redirect('sales')

    entries = SalesEntry.objects.filter(user=request.user)\
        .prefetch_related('wishes', 'chat_messages')\
        .order_by('-created_at')

    return render(request, 'contact/sales.html', {'entries': entries, 'user_groups': user_groups})

@login_required
def sales_chat(request, entry_id):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    entry = get_object_or_404(SalesEntry, id=entry_id)

    # Zugriff nur für Ersteller oder Admin
    if request.user != entry.user and not request.user.is_staff:
        raise PermissionDenied("Du hast keinen Zugriff auf diesen Chat.")

    # Neue Nachricht senden
    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            SalesChatMessage.objects.create(
                entry=entry,
                user=request.user,
                message=message_text
            )
            return redirect('sales_chat', entry_id=entry.id)

    # Alle Nachrichten für diesen Eintrag
    messages = SalesChatMessage.objects.filter(entry=entry).order_by('created_at')

    return render(request, 'contact/sales_chat.html', {
        'entry': entry,
        'messages': messages,
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
        messages.success(request, "Ticket erfolgreich erstellt.")
        return redirect('support_tickets')

    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')  # hier auch "user"
    return render(request, 'contact/support.html', {'form': form, 'tickets': tickets, 'user_groups': user_groups})

@login_required
def ticket_detail(request, ticket_number):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number)

    # Nur Zugriff, wenn eigener User oder Admin
    if ticket.user != request.user and not request.user.is_staff:
        messages.error(request, "Du hast keinen Zugriff auf dieses Ticket.")
        return redirect('support_tickets')

    if request.method == 'POST':
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender = request.user
            message.save()

            # Ticket ggf. reaktivieren
            ticket.reactivate_if_new_message(request.user)
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
