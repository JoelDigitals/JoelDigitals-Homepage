"""
CRON JOB KONFIGURATION - KOMPLETTE ANLEITUNG
"""

# ============================================
# 1. RENDER.COM (EMPFOHLEN)
# ============================================

# Datei: Procfile (im Projektroot)
"""
web: gunicorn joel_digitals.wsgi:application --log-file - --timeout 120
worker: python manage.py order_automation --all
background: curl -X GET https://www.joel-digitals.de/shop/automation/cron/ 2>/dev/null
scheduler: python manage.py order_automation --all
"""

# Render Environment Variables (.env):
CRON_SECRET_TOKEN=your-secret-token-here
ALLOWED_HOSTS=www.joel-digitals.de,joel-digitals.de


# ============================================
# 2. HEROKU
# ============================================

# Terminal Commands:
"""
heroku addons:create scheduler:standard
heroku addons:open scheduler
"""

# Dann im Web-UI einen neuen Job hinzufügen:
Job: python manage.py order_automation --all
Frequenz: Every 10 minutes


# ============================================
# 3. LINUX CRON (LOKAL)
# ============================================

# Terminal:
crontab -e

# Dann hinzufügen:
"""
# Run automation every 10 minutes
*/10 * * * * curl -X GET https://www.joel-digitals.de/shop/automation/cron/ -H "Authorization: Bearer your-secret-token" >> /var/log/joel_digitals_cron.log 2>&1

# Alternative mit Django Management Command
*/10 * * * * cd /path/to/joel_digitals && /path/to/venv/bin/python manage.py order_automation --all >> /var/log/joel_digitals_cron.log 2>&1

# Oder Alternative mit Python Script
*/10 * * * * /path/to/joel_digitals/run_cron.sh >> /var/log/joel_digitals_cron.log 2>&1
"""

# Datei: /path/to/joel_digitals/run_cron.sh
#!/bin/bash
cd /path/to/joel_digitals
source /path/to/venv/bin/activate
python manage.py order_automation --all


# ============================================
# 4. DOCKER / KUBERNETES
# ============================================

# Dockerfile - Multi-stage für CronJob
"""
FROM python:3.11-slim AS base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Production
FROM base AS production
CMD ["gunicorn", "joel_digitals.wsgi:application"]

# CronJob
FROM base AS cronjob
CMD ["python", "manage.py", "order_automation", "--all"]
"""

# Kubernetes CronJob (k8s)
"""
apiVersion: batch/v1
kind: CronJob
metadata:
  name: order-automation
spec:
  schedule: "*/10 * * * *"  # Alle 10 Minuten
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: order-automation
            image: registry.example.com/joel-digitals:cronjob
            env:
            - name: DJANGO_SETTINGS_MODULE
              value: "joel_digitals.settings"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
          restartPolicy: OnFailure
"""


# ============================================
# 5. PYTHON SCRIPT (APScheduler)
# ============================================

# Datei: manage.py oder separate run_scheduler.py
"""
import schedule
import time
from django.core.management import execute_from_command_line
from shop_ourapps.services.automation_service import OrderAutomationService

def job():
    print("[*] Running automated tasks...")
    OrderAutomationService.auto_deliver_after_30_minutes()
    OrderAutomationService.send_review_emails()
    print("[✓] Tasks completed!")

# Schedule every 10 minutes
schedule.every(10).minutes.do(job)

# Run scheduler
if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds
"""

# Terminal:
# python run_scheduler.py


# ============================================
# 6. WINDOWS TASK SCHEDULER
# ============================================

# Task Scheduler GUI:
# 1. Öffne "Task Scheduler"
# 2. Create Basic Task
# 3. Name: "Joel Digitals Order Automation"
# 4. Trigger: Custom (Recurring) every 10 minutes
# 5. Action:
#    Program: C:\Python311\python.exe
#    Arguments: C:\path\to\manage.py order_automation --all
# 6. Settings: "Run immediately" if missed

# Alternative mit PowerShell:
# $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 10) -At (Get-Date)
# $action = New-ScheduledTaskAction -Execute "C:\Python311\python.exe" -Argument "C:\path\manage.py order_automation --all"
# Register-ScheduledTask -TaskName "OrderAutomation" -Trigger $trigger -Action $action


# ============================================
# 7. DJANGO Q (ASYNC TASK QUEUE)
# ============================================

# settings.py
Q_CLUSTER = {
    'name': 'joel_digitals',
    'workers': 4,
    'timeout': 300,
    'retry': 360,
    'queue_limit': 50,
    'django_redis': 'default',
    'ack_failures': True,
    'schedule': {
        'order_automation': {
            'func': 'shop_ourapps.services.automation_service.OrderAutomationService.auto_deliver_after_30_minutes',
            'schedule': timedelta(minutes=10),
        },
        'send_reviews': {
            'func': 'shop_ourapps.services.automation_service.OrderAutomationService.send_review_emails',
            'schedule': timedelta(minutes=10),
        }
    }
}

# Terminal:
# python manage.py qcluster


# ============================================
# 8. CELERY + BEAT (PRODUCTION EMPFOHLEN)
# ============================================

# requirements.txt
celery==5.3.0
celery-beat==2.5.0
redis==5.0.0

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Berlin'

CELERY_BEAT_SCHEDULE = {
    'auto-deliver-orders': {
        'task': 'shop_ourapps.tasks.auto_deliver_orders',
        'schedule': timedelta(minutes=10),
    },
    'send-review-emails': {
        'task': 'shop_ourapps.tasks.send_review_emails',
        'schedule': timedelta(minutes=10),
    },
}

# Datei: shop_ourapps/tasks.py
from celery import shared_task
from shop_ourapps.services.automation_service import OrderAutomationService

@shared_task
def auto_deliver_orders():
    return OrderAutomationService.auto_deliver_after_30_minutes()

@shared_task
def send_review_emails():
    return OrderAutomationService.send_review_emails()

# Terminal - Worker starten:
# celery -A joel_digitals worker -l info

# Terminal - Beat Scheduler starten:
# celery -A joel_digitals beat -l info


# ============================================
# SICHERHEITS-TIPPS
# ============================================

# 1. Token-basierte Authentifizierung (views.py)
@csrf_exempt
@require_http_methods(["GET", "POST"])
def automation_cron(request):
    """Sichere Version mit Token"""
    from django.conf import settings
    
    token = request.GET.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    expected_token = getattr(settings, 'CRON_SECRET_TOKEN', None)
    
    if not expected_token or token != expected_token:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # ... rest der logic


# 2. IP-Whitelist (views.py)
from django.http import HttpRequest

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
def automation_cron(request):
    ALLOWED_IPS = ['127.0.0.1', '::1', 'render-server-ip']  # Whitelist
    client_ip = get_client_ip(request)
    
    if client_ip not in ALLOWED_IPS:
        return JsonResponse({'error': 'IP not whitelisted'}, status=403)
    
    # ... rest der logic


# 3. Rate Limiting
from django.core.cache import cache

@csrf_exempt
def automation_cron(request):
    cache_key = 'automation_cron_last_run'
    last_run = cache.get(cache_key)
    
    if last_run:
        return JsonResponse({'error': 'Already running'}, status=429)
    
    cache.set(cache_key, True, timeout=60)  # 60 Sek. Lock
    
    try:
        # ... logic
    finally:
        cache.delete(cache_key)


# ============================================
# MONITORING & LOGGING
# ============================================

# settings.py - Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/joel_digitals_automation.log',
        },
    },
    'loggers': {
        'shop_ourapps.automation': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# views.py - Logging
import logging
logger = logging.getLogger('shop_ourapps.automation')

@csrf_exempt
def automation_cron(request):
    try:
        logger.info("CronJob started")
        delivery_count = OrderAutomationService.auto_deliver_after_30_minutes()
        review_count = OrderAutomationService.send_review_emails()
        logger.info(f"CronJob completed: {delivery_count} delivered, {review_count} reviews sent")
        return JsonResponse({...})
    except Exception as e:
        logger.error(f"CronJob failed: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# MONITORING DASHBOARD
# ============================================

# URLs können überwacht werden via UptimeRobot, Pingdom, etc.
# https://www.joel-digitals.de/shop/automation/cron/?token=your-secret

# Oder mit Webhook (Slack/Discord Notifications)
def send_notification(success, message):
    import requests
    webhook_url = getattr(settings, 'SLACK_WEBHOOK', None)
    if webhook_url:
        requests.post(webhook_url, json={
            'text': f"{'✅' if success else '❌'} Order Automation: {message}"
        })
