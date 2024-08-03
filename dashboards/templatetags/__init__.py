from django.apps import AppConfig

class DashboardsConfig(AppConfig):
    name = 'dashboards'

    def ready(self):
        import dashboards.templatetags.custom_filters
