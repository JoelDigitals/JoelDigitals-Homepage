from django import forms

class PurchaseForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=255)
    email = forms.EmailField(label="Email")
    address = forms.CharField(label="Address", widget=forms.Textarea)
    zip_code = forms.CharField(label="ZIP Code")
    city = forms.CharField(label="City")
    country = forms.CharField(label="Country")

class VoucherPurchaseForm(forms.Form):
    amount = forms.DecimalField(min_value=1, label="Betrag (€)")
    payment_method = forms.ChoiceField(choices=[('wallet', 'Wallet')], label="Zahlungsmethode")
    recipient_email = forms.EmailField(label="E-Mail des Empfängers")
    recipient_name = forms.CharField(max_length=100, label="Name des Empfängers")
    message = forms.CharField(widget=forms.Textarea, required=False, label="Nachricht")
    design = forms.ChoiceField(
        choices=[
            ('default', 'Standard'),
            ('happy_birthday', '🎉 Happy Birthday'),
            ('danke', '🙏 Danke'),
            ('fuer_dich', '🎁 Für Dich'),
        ],
        label="Designauswahl"
    )