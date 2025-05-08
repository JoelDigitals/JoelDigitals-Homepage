from django import forms
from .models import SalesEntry, SupportTicket, TicketMessage, SalesWish
from django.contrib.auth.models import User


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

class SalesEntryForm(forms.ModelForm):
    class Meta:
        model = SalesEntry
        fields = ['name', 'email', 'subject', 'message']

class SalesWishForm(forms.ModelForm):
    class Meta:
        model = SalesWish
        fields = ['title', 'description']


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['name', 'email', 'subject', 'description']  # keine priority, kein user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # user und priority nicht im Formular enthalten – werden automatisch gesetzt

class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Nachricht schreiben...'}),
        }
