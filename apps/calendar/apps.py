from django.apps import AppConfig


class CalendarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calendar"
    verbose_name = "Super Calendar"

    def ready(self):
        # Import signals when app is ready
        import apps.calendar.signals
