from django.apps import AppConfig

class DataCleaningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_cleaning'

    def ready(self):
        import data_cleaning.signals
