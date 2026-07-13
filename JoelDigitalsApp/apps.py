from django.apps import AppConfig


class JoeldigitalsappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'JoelDigitalsApp'
    verbose_name = 'Joel Digitals App'

    def ready(self):
        from . import signals  # noqa: F401
