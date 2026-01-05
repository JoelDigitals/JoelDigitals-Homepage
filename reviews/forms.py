from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["name", "email", "rating", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
            "rating": forms.RadioSelect(choices=[(i, f"{i} Sterne") for i in range(1,6)])
        }
