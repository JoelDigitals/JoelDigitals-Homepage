from datetime import timedelta, datetime
from django.utils.timezone import make_aware
from .models import Appointment, TimeSlot, SpecialTimeSlot
import datetime as dt


def get_available_times(date):
    """Erzeugt 5-Minuten-Slots basierend auf Regular + Special Times"""

    weekday = date.weekday()
    slots = []

    regular = TimeSlot.objects.filter(weekday=weekday)
    specials = SpecialTimeSlot.objects.filter(date=date)

    time_ranges = []

    for r in regular:
        time_ranges.append((r.start_time, r.end_time))

    for s in specials:
        time_ranges.append((s.start_time, s.end_time))

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
