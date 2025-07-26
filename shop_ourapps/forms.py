from django import forms

class PurchaseForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=255)
    email = forms.EmailField(label="Email")
    address = forms.CharField(label="Address", widget=forms.Textarea)
    zip_code = forms.CharField(label="ZIP Code")
    city = forms.CharField(label="City")
    country = forms.CharField(label="Country")

DESIGN_CHOICES = [
    ('happy_birthday', 'Happy Birthday'),
    ('thanks', 'Thank You'),
    ('love_you', 'I love You'),
    ('default', 'Standard'),
]

class VoucherPurchaseForm(forms.Form):
    amount = forms.DecimalField(label="Amount (€)", min_value=1, decimal_places=2)
    payment_method = forms.ChoiceField(
        label="Zahlungsmethode",
        choices=[
            ('wallet', 'Wallet'),
        ]
    )
    recipient_email = forms.EmailField(label="Your Email")
    recipient_name = forms.CharField(label="Recipient Name", max_length=100)
    message = forms.CharField(label="Personal Massage max. 100", widget=forms.Textarea, required=False, max_length=100)
    design = forms.ChoiceField(label="Design", choices=DESIGN_CHOICES, widget=forms.RadioSelect, initial='default')