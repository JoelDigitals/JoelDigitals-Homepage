from django import forms

class PurchaseForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=255)
    email = forms.EmailField(label="Email")
    address = forms.CharField(label="Address", widget=forms.Textarea)
    zip_code = forms.CharField(label="ZIP Code")
    city = forms.CharField(label="City")
    country = forms.CharField(label="Country")
