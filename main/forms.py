from django import forms
from .models import FAQ

class FAQSearchForm(forms.Form):
    q = forms.CharField(
        label="Suche",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Frage oder Stichwort..."}),
    )

class AskQuestionForm(forms.ModelForm):
    class Meta:
        model = FAQ
        # richtige Felder aus deinem Modell
        fields = (
            "question_de", "question_en",
            "short_answer_de", "short_answer_en",
            "answer_de", "answer_en",
        )
        widgets = {
            "question_de": forms.TextInput(attrs={"placeholder": "Deine Frage auf Deutsch"}),
            "question_en": forms.TextInput(attrs={"placeholder": "Your question in English"}),
            "short_answer_de": forms.Textarea(attrs={"rows": 3}),
            "short_answer_en": forms.Textarea(attrs={"rows": 3}),
            "answer_de": forms.Textarea(attrs={"rows": 5}),
            "answer_en": forms.Textarea(attrs={"rows": 5}),
        }

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("Email address"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@email.com')
        })
    )

    accept_agb = forms.BooleanField(
        required=True,
        label=_("I agree to the Terms and Conditions")
    )

    accept_privacy = forms.BooleanField(
        required=True,
        label=_("I agree to the Privacy Policy")
    )

    accept_contact = forms.BooleanField(
        required=True,
        label=_(
            "I agree to be contacted using my provided data (e.g. email) "
            "for information about price changes or service updates"
        )
    )

    accept_marketing = forms.BooleanField(
        required=False,
        label=_("I would like to receive marketing emails (optional)")
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Username')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Password')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirm password')
        })