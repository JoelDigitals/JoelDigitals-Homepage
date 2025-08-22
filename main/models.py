from django.db import models

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