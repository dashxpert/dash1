
from django.apps import AppConfig

class webscrapingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webscraping'

    def ready(self):
        import webscraping.signals  # Ensure this line is added
