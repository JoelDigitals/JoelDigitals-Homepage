from django import forms

class TeachForm(forms.Form):
    message = forms.CharField(
        label="Thema / Frage",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    answer = forms.CharField(
        label="Antwort / Beschreibung",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5})
    )
    lang = forms.ChoiceField(
        label="Sprache",
        choices=[("de", "Deutsch"), ("en", "Englisch")],
        initial="de",
        widget=forms.Select(attrs={"class": "form-select"})
    )
