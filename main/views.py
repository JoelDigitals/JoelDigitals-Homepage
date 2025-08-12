from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TeamMember

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
    return render(request, 'main/home.html', {'user_groups': user_groups})

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
    # Hier kannst du bei Bedarf weitere Daten an das Template geben
    opening_times = {
        "Monday": "4 PM – 6 PM",
        "Wednesday": "4 PM – 6 PM",
        "Thursday": "4 PM – 5 PM",
        "Saturday": "1 PM – 3 PM",
    }
    closed_days = ["Tuesday", "Friday", "Sunday"]
    context = {
        "opening_times": opening_times,
        "closed_days": closed_days,
        "phone_number": "+49 1525 3480270",
    }
    return render(request, "main/opening_hours.html", context)