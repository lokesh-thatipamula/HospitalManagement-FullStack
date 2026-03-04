from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'

    def ready(self):
        import sys
        if 'runserver' in sys.argv:
            from hospital_backend.api.scheduler import start_scheduler
            start_scheduler()
