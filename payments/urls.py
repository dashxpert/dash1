# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('payment/', views.payment_page, name='payment_page'),
    path('payment/paypal/', views.paypal_payment, name='paypal_payment'),
    path('payment/razorpay/', views.razorpay_payment, name='razorpay_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='failure'),
    path('prompt_payment/', views.prompt_payment, name='prompt_payment'),
]
