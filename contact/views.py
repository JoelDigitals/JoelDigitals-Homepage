from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from .forms import ContactForm, SalesWishForm, SupportTicketForm, TicketMessageForm
from django.contrib import messages
from django.http import HttpResponse
from .models import SalesWish, SupportTicket, TicketMessage, SalesChatMessage, SalesEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def index(request):
    return render(request, 'contact/index.html')

def contact_view(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        name = form.cleaned_data['name']
        message = form.cleaned_data['message']

        send_mail(
            subject=f"Kontaktanfrage von {name}, Email: {form.cleaned_data['email']}",
            message=message,
            from_email='joel-digitals@gmx.de',
            recipient_list=['joel-digitals@gmx.de'],
        )

        messages.success(request, "Deine Nachricht wurde erfolgreich gesendet.")
        return redirect('contact_form')

    return render(request, 'contact/contact.html', {'form': form})

@login_required
def sales(request):
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

    return render(request, 'contact/sales.html', {'entries': entries})

@login_required
def sales_chat(request, entry_id):
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
        'messages': messages
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
    return render(request, 'contact/support.html', {'form': form, 'tickets': tickets})


@login_required
def ticket_detail(request, ticket_number):
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
            return redirect('ticket_detail', ticket_number=ticket.ticket_number)
    else:
        form = TicketMessageForm()

    messages_list = ticket.messages.order_by('created_at')

    return render(request, 'contact/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages_list,
        'form': form,
    })

@staff_member_required
def admin_ticket_view(request):
    tickets = SupportTicket.objects.all().order_by('-created_at')
    if request.method == "POST":
        ticket_id = request.POST.get("ticket_id")
        action = request.POST.get("action")
        ticket = SupportTicket.objects.get(id=ticket_id)
        if action == "toggle":
            ticket.is_resolved = not ticket.is_resolved
            ticket.save()
    return render(request, 'contact/admin_tickets.html', {'tickets': tickets})

@staff_member_required
def admin_sales_view(request):
    entries = SalesEntry.objects.all().order_by('-created_at')
    return render(request, 'contact/admin_sales.html', {'entries': entries})

def sales_entry_detail(request, entry_id):
    entry = get_object_or_404(SalesEntry, id=entry_id)
    wishes = entry.wishes.all()
    return render(request, 'contact/sales_entry_detail.html', {'entry': entry, 'wishes': wishes})

def add_wish(request, entry_id):
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

    return render(request, 'contact/wish_form.html', {'form': form, 'title': 'Neuen Wunsch hinzufügen'})

def edit_wish(request, entry_id, wish_id):
    wish = get_object_or_404(SalesWish, pk=wish_id)
    if request.method == 'POST':
        form = SalesWishForm(request.POST, instance=wish)
        if form.is_valid():
            form.save()
            return redirect('sales_entry_detail', entry_id=entry_id)
    else:
        form = SalesWishForm(instance=wish)
    return render(request, 'contact/wish_form.html', {'form': form, 'title': 'Wunsch bearbeiten'})

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

