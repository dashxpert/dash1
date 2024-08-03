from django.urls import path
from .views import HomeView, ServicesView ,PricingView, UploadFileView, Dashboard, UserProfileView
from . import views  # Import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # This handles the root URL for the app
    path('services/', ServicesView.as_view(), name='services'),
    path('pricing/', PricingView.as_view(), name='pricing'),

    path('upload-dashboard/', UploadFileView.as_view(), name='upload-dashboard'),
    path('dashboard-chart/', Dashboard.as_view(), name='dashboard-chart'),
    path('user_profile/', UserProfileView.as_view(), name='user_profile'),
    
    path('about-us/', views.about_us, name='about_us'),

    # Contact Us page
    path('contact-us/', views.contact_us, name='contact_us'),

    # Privacy Policy page
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    # Terms & Conditions page
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),

    # Cancellation/Refund Policies page
    path('cancellation-refund-policies/', views.cancellation_refund_policies, name='cancellation_refund_policies'),

]
 

    
