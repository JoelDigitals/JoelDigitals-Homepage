from django.db import models
from django.utils.translation import get_language
from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.urls import reverse

class FAQ(models.Model):
    """
    Zweisprachige FAQ: Deutsch & Englisch
    """
    # DE / EN Felder
    question_de = models.CharField("Frage (Deutsch)", max_length=255)
    question_en = models.CharField("Question (English)", max_length=255, blank=True)

    short_answer_de = models.TextField("Kurzantwort (DE)", blank=True)
    short_answer_en = models.TextField("Short Answer (EN)", blank=True)

    answer_de = RichTextField("Antwort (DE)", blank=True)
    answer_en = RichTextField("Answer (EN)", blank=True)

    detail_content_de = RichTextField("Detailseite Inhalt (DE)", blank=True)
    detail_content_en = RichTextField("Detail Page Content (EN)", blank=True)

    # Allgemein
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Kleinere Zahl = weiter oben")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "question_de")
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question_de or "FAQ"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.question_en or self.question_de)[:200]
            slug = base
            counter = 1
            while FAQ.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("detail", kwargs={"slug": self.slug})

    # === Hilfsfunktionen ===
    def get_lang_field(self, base_name):
        lang = get_language()
        if lang.startswith("de"):
            return getattr(self, f"{base_name}_de")
        else:
            return getattr(self, f"{base_name}_en") or getattr(self, f"{base_name}_de")

    # Kurzformen:
    @property
    def question(self):
        return self.get_lang_field("question")

    @property
    def short_answer(self):
        return self.get_lang_field("short_answer")

    @property
    def answer(self):
        return self.get_lang_field("answer")

    @property
    def detail_content(self):
        return self.get_lang_field("detail_content")

# Create your models here.
class TeamMember(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='team_photos/')
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
from django.utils.translation import gettext_lazy as _

class OpeningHour(models.Model):
    class Weekday(models.TextChoices):
        MONDAY = "Monday", _("Monday")
        TUESDAY = "Tuesday", _("Tuesday")
        WEDNESDAY = "Wednesday", _("Wednesday")
        THURSDAY = "Thursday", _("Thursday")
        FRIDAY = "Friday", _("Friday")
        SATURDAY = "Saturday", _("Saturday")
        SUNDAY = "Sunday", _("Sunday")

    weekday = models.CharField(max_length=10, choices=Weekday.choices, unique=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    closed = models.BooleanField(default=False)

    def __str__(self):
        if self.closed:
            return f"{self.weekday}: Closed"
        return f"{self.weekday}: {self.open_time.strftime('%H:%M')} – {self.close_time.strftime('%H:%M')}"


class SpecialOpeningHour(models.Model):
    date = models.DateField(unique=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    closed = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        if self.closed:
            return f"{self.date} (Closed)"
        return f"{self.date}: {self.open_time.strftime('%H:%M')} – {self.close_time.strftime('%H:%M')}"