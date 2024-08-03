from django.urls import path
from .views import WebScrapingView, download_excel

urlpatterns = [
    path('webscraping/', WebScrapingView.as_view(), name='webscraping'),
    path('webscraping/download_excel/', download_excel, name='download_excel'),
]
