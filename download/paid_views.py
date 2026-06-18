from django.shortcuts import render, get_object_or_404, redirect
from .models import DownloadPackage, DownloadPackageApp, AccessCode, CodeRedemption, DownloadSession, AccessSuspension
from django.utils import timezone
import datetime


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')


def _get_ua(request):
    return request.META.get('HTTP_USER_AGENT', '')


def _check_abuse(ip):
    now = timezone.now()
    if CodeRedemption.objects.filter(ip_address=ip, redeemed_at__gte=now - datetime.timedelta(hours=1)).count() > 10:
        AccessSuspension.objects.get_or_create(ip_address=ip, is_active=True,
            defaults={'reason': f'Auto: {ip} - too many redemptions'})
        return True
    if DownloadSession.objects.filter(ip_address=ip, downloaded_at__gte=now - datetime.timedelta(minutes=10)).count() > 50:
        AccessSuspension.objects.get_or_create(ip_address=ip, is_active=True,
            defaults={'reason': f'Auto: {ip} - too many downloads'})
        return True
    return AccessSuspension.objects.filter(ip_address=ip, is_active=True).exists()


def home(request):
    ip = _get_ip(request)
    suspended = _check_abuse(ip)
    return render(request, 'downloads/paid_home.html', {
        'packages': DownloadPackage.objects.filter(is_active=True),
        'suspended': suspended,
        'error': request.GET.get('error', ''),
    })


def redeem(request):
    if request.method != 'POST':
        return redirect('paid_home')

    code_str = request.POST.get('code', '').strip().upper()
    ip = _get_ip(request)

    if _check_abuse(ip):
        return redirect('/paid-downloads/?error=suspended')

    code = AccessCode.objects.filter(code=code_str).first()
    if not code or not code.is_valid():
        return redirect('/paid-downloads/?error=' + ('expired' if code else 'invalid'))

    code.used_count += 1
    code.save(update_fields=['used_count'])

    red = CodeRedemption.objects.create(
        code=code, ip_address=ip,
        user_agent=_get_ua(request),
        device_info=request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
    )
    request.session['paid_token'] = f'{red.id}:{code.package_id}'
    return redirect('paid_portal', package_id=code.package_id)


def portal(request, package_id):
    token = request.session.get('paid_token', '')
    package = get_object_or_404(DownloadPackage, id=package_id, is_active=True)
    ip = _get_ip(request)
    suspended = _check_abuse(ip)
    has_access = str(package_id) in token.split(':')[-1] if ':' in token else False

    apps = DownloadPackageApp.objects.filter(package=package).select_related('app', 'os', 'download') if has_access else []

    return render(request, 'downloads/paid_portal.html', {
        'package': package,
        'package_apps': apps,
        'has_access': has_access,
        'suspended': suspended,
    })


def download_file(request, app_id):
    token = request.session.get('paid_token', '')
    if not token or ':' not in token:
        return redirect('paid_home')

    pa = get_object_or_404(DownloadPackageApp, id=app_id)
    ip = _get_ip(request)

    if _check_abuse(ip):
        return render(request, 'downloads/paid_suspended.html', {})

    try:
        red_id = int(token.split(':')[0])
        red = CodeRedemption.objects.get(id=red_id)
    except (ValueError, CodeRedemption.DoesNotExist):
        return redirect('paid_home')

    if str(pa.package_id) != token.split(':')[-1]:
        return redirect('paid_home')

    DownloadSession.objects.create(
        redemption=red, package_app=pa,
        ip_address=ip, user_agent=_get_ua(request),
    )

    url = pa.get_link()
    return redirect(url) if url else redirect('paid_portal', package_id=pa.package_id)
