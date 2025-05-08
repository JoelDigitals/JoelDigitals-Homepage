from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages

def imprint_view(request):
    return render(request, 'legal/imprint.html')

def privacy_view(request):
    return render(request, 'legal/privacy.html')

def terms_view(request):
    return render(request, 'legal/terms.html')

# Create your views here.
def home(request):
    return render(request, 'main/home.html')

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
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # oder eine andere Zielseite
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def about_view(request):
    return render(request, 'main/about.html')

def service_view(request):
    return render(request, 'main/services.html')