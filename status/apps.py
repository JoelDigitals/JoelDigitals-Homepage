from django.apps import AppConfig
import os


class StatusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'status'

    def ready(self):
        _start_scheduler()


def _start_scheduler():
    if os.environ.get('RUN_MAIN') != 'true' and os.environ.get('WSGI') != 'true':
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from status.checker import check_all_apps

        scheduler = BackgroundScheduler()
        scheduler.add_job(check_all_apps, 'interval', minutes=3, id='status_check', replace_existing=True)
        scheduler.start()
    except Exception:
        pass
