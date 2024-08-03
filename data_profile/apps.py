from django.apps import AppConfig

class DataProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_profile'

    def ready(self):
        import data_profile.signals  # Ensure this line is added
