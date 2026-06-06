from django import forms
from .models import SalesEntry, SupportTicket, TicketMessage, SalesWish, TicketNote, Appointment
from shop_ourapps.models import App
from django.contrib.auth.models import User
from django.forms.widgets import DateTimeInput

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'appointment_type',
            'appointment_datetime'
        ]
        widgets = {
            'appointment_datetime': DateTimeInput(attrs={
                'type': 'datetime-local'
            })
        }


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    # Honeypot - unsichtbar per CSS im Template, nie per required/widget verstecken
    hp_url = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_hp_url(self):
        if self.cleaned_data.get('hp_url'):
            raise forms.ValidationError("Bot erkannt.")
        return ''

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
        fields = ['name', 'email', 'subject', 'description', 'app_name', 'platform']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['app_name'].queryset = App.objects.filter(is_active=True)


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Nachricht schreiben...'}),
        }

class TicketNoteForm(forms.ModelForm):
    class Meta:
        model = TicketNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Interne Notiz hinzufügen...'}),
        }