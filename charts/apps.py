

# dashboards/apps.py
from django.apps import AppConfig

class chartsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'charts'

    def ready(self):
        import charts.signals

