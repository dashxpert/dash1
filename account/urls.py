
# accounts/urls.py
from django.urls import path
from .views import register, user_login, user_logout, thank_you, verify_otp

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('thank_you/', thank_you, name='thank_you'),
    path('otp_verification/', verify_otp, name='otp_verification'),
]

