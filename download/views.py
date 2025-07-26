from django.shortcuts import render, get_object_or_404
from .models import App, OperatingSystem
from django.utils.timezone import localdate

def app_list(request):
    apps = App.objects.all()
    return render(request, 'downloads/app_list.html', {'apps': apps})

def app_detail(request, app_id):
    app = get_object_or_404(App, pk=app_id)

    today = localdate()  # aktuelles Datum ohne Uhrzeit

    # Filter nach Release-Datum <= heute und sortieren
    downloads = app.downloads.select_related('operating_system') \
        .filter(release_date__lte=today) \
        .order_by('-release_date', '-id')

    os_filter = request.GET.get('os')
    if os_filter:
        downloads = downloads.filter(operating_system__name__iexact=os_filter)

    operating_systems = OperatingSystem.objects.all()

    return render(request, 'downloads/app_detail.html', {
        'app': app,
        'downloads': downloads,
        'operating_systems': operating_systems,
        'selected_os': os_filter,
    })