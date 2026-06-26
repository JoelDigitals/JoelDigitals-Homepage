from django import forms
from .models import WebinarRegistration


class WebinarRegistrationForm(forms.ModelForm):
    class Meta:
        model = WebinarRegistration
        fields = []  # Nur CSRF-Schutz, keine Benutzereingaben nötig
