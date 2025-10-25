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
