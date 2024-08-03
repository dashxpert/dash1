from django.urls import path
from .views import  DataProfileView 
from . import views  # Import views

urlpatterns = [
    
    
    path('profile/', DataProfileView.as_view(), name='profile'),
    
       
]

