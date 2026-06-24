import re
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from .models import AutoUpdateApp


def parse_version(version_str):
    parts = version_str.strip().split('.')
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


@csrf_exempt
@require_GET
def check_version(request, app_slug):
    current_version = request.GET.get('current_version', '')
    if not current_version:
        return JsonResponse(
            {'error': 'current_version parameter is required'},
            status=400
        )

    current_parsed = parse_version(current_version)
    if current_parsed is None:
        return JsonResponse(
            {'error': 'Invalid version format. Use format: 1.0.0.0'},
            status=400
        )

    try:
        app = AutoUpdateApp.objects.prefetch_related('versions').get(
            slug=app_slug, versions__is_active=True
        )
    except AutoUpdateApp.DoesNotExist:
        return JsonResponse(
            {'error': 'App not found'},
            status=404
        )

    versions = app.versions.filter(is_active=True)
    latest = versions.first()

    if not latest:
        return JsonResponse({
            'update_available': False,
            'current_version': current_version,
            'latest_version': None,
            'message': 'No versions available'
        })

    latest_parsed = parse_version(latest.version)
    update_available = latest_parsed is not None and latest_parsed > current_parsed

    return JsonResponse({
        'update_available': update_available,
        'current_version': current_version,
        'latest_version': latest.version,
        'download_link': latest.download_link if update_available else None,
        'release_date': latest.release_date.isoformat() if update_available else None,
        'release_notes': latest.release_notes if update_available else None,
        'message': 'Update available' if update_available else 'You have the latest version'
    })


@require_GET
def app_list(request):
    apps = AutoUpdateApp.objects.all().values('name', 'slug')
    return JsonResponse(list(apps), safe=False)


@require_GET
def all_versions(request, app_slug):
    try:
        app = AutoUpdateApp.objects.get(slug=app_slug)
    except AutoUpdateApp.DoesNotExist:
        return JsonResponse({'error': 'App not found'}, status=404)

    versions = app.versions.filter(is_active=True).values(
        'version', 'release_date', 'download_link', 'release_notes'
    )
    return JsonResponse(list(versions), safe=False)
