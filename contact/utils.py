from datetime import timedelta, datetime
from django.utils.timezone import make_aware
from .models import Appointment, TimeSlot, SpecialTimeSlot
import datetime as dt


def get_available_times(date):
    """Erzeugt 5-Minuten-Slots basierend auf Regular + Special Times.
    Special times haben Vorrang vor regulären times."""

    weekday = date.weekday()
    slots = []

    specials = SpecialTimeSlot.objects.filter(date=date)

    if specials.exists():
        # Spezielle Zeiten haben Vorrang
        open_specials = specials.filter(is_closed=False)
        if not open_specials.exists():
            return []
        time_ranges = [(s.start_time, s.end_time) for s in open_specials]
    else:
        regular = TimeSlot.objects.filter(weekday=weekday)
        time_ranges = [(r.start_time, r.end_time) for r in regular]

    for start, end in time_ranges:
        current = dt.datetime.combine(date, start)
        end_dt = dt.datetime.combine(date, end)
        while current < end_dt:
            slots.append(current)
            current += timedelta(minutes=5)

    return slots


def is_slot_available(dt_start, duration):
    """Überprüft ob maximal 2 Termine gleichzeitig liegen"""

    dt_end = dt_start + timedelta(minutes=duration)

    overlapping = Appointment.objects.filter(
        appointment_datetime__lt=dt_end,
        status__in=['pending', 'accepted']
    ).count()

    return overlapping < 2
