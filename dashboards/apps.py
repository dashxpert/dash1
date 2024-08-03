

# dashboards/apps.py
from django.apps import AppConfig

class DashboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboards'

    def ready(self):
        import dashboards.signals

