from django.contrib import admin
from django.urls import path, include
from dashboards.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboards.urls')),
    path('account/', include('account.urls')),
    #path('blogs/', include('blogs.urls')),
    path('charts/', include('charts.urls')),
    path('anamoly_detection/', include('anamoly_detection.urls')),
    path('webscraping/', include('webscraping.urls')),
    path('data_profile/', include('data_profile.urls')),
    path('payments/', include('payments.urls')),
    path('data_cleaning/', include('data_cleaning.urls')),
    path('join_append/', include('join_append.urls')),
    path('', include('pivot_service.urls')),
]
