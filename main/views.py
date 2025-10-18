from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TeamMember, OpeningHour, SpecialOpeningHour
from blog.models import BlogPost
from shop_ourapps.models import App
from datetime import date, timedelta
import random


def imprint_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/imprint.html', {'user_groups': user_groups})

def privacy_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/privacy.html', {'user_groups': user_groups})

def terms_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'legal/terms.html', {'user_groups': user_groups})

# Create your views here.
def home(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []

    # Neuster Blogartikel
    latest_blog = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:2]

    # 3 zufällige Produkte
    products = list(App.objects.filter(is_available_for_purchase=True))
    random_products = random.sample(products, min(len(products), 3))

    return render(request, 'main/home.html', {
        'user_groups': user_groups,
        'latest_blog': latest_blog,
        'products': random_products
    })

#register 
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registrierung erfolgreich! Du kannst dich jetzt einloggen.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # oder eine andere Zielseite
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form, 'user_groups': user_groups})

from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')  # KEINE weiteren Argumente hier


def about_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'main/about.html', {'user_groups': user_groups})

def service_view(request):
    user_groups = [group.name for group in request.user.groups.all()] if request.user.is_authenticated else []
    return render(request, 'main/services.html', {'user_groups': user_groups})

def team_view(request):
    members = TeamMember.objects.all()
    return render(request, 'main/team.html', {'members': members})


def opening_hours(request):
    today = date.today()
    today_name = today.strftime("%A")
    end_date = today + timedelta(days=6)  # heute + 6 Tage

    # Basiszeiten (Normalplan)
    base_hours = {
        oh.weekday: (
            "Closed"
            if oh.closed
            else f"{oh.open_time.strftime('%H:%M')} – {oh.close_time.strftime('%H:%M')}"
        )
        for oh in OpeningHour.objects.all()
    }

    # Sonderzeiten nur für heute bis 6 Tage später
    specials = SpecialOpeningHour.objects.filter(
        date__gte=today, date__lte=end_date
    ).order_by("date")

    # Mapping für kommende Sonderzeiten pro Wochentag
    special_overrides = {}
    for s in specials:
        weekday_name = s.date.strftime("%A")
        special_overrides[weekday_name] = (
            "Closed"
            if s.closed
            else f"{s.open_time.strftime('%H:%M')} – {s.close_time.strftime('%H:%M')}"
        )

    # Heute überschreiben, falls Sonderzeit existiert
    if today_name in special_overrides:
        base_hours[today_name] = special_overrides[today_name]

    # Montag → Sonntag sortieren
    days_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    ordered_times = {}
    for day in days_order:
        if day in special_overrides:
            ordered_times[day] = " *" + special_overrides[day]  # Sternchen für Sonderzeit
        else:
            ordered_times[day] = base_hours.get(day, "Closed")

    context = {
        "opening_times": ordered_times,
        "today": today_name,
        "phone_number": "+49 1525 3480270",
    }
    return render(request, "main/opening_hours.html", context)