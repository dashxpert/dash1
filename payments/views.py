# views.py
from django.shortcuts import render, redirect
from django.conf import settings
from .models import Payment
from django.contrib.auth.decorators import login_required
import razorpay

@login_required
def payment_page(request):
    return render(request, 'payment_page.html')

from django.urls import reverse

from datetime import timedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from dashboards.models import Profile  # Make sure to import the Payment model

import razorpay

@login_required
def paypal_payment(request):
    if request.method == 'POST':
        payment = Payment.objects.create(
            user=request.user,
            payment_method='paypal',
            transaction_id='PAYPAL_TRANSACTION_ID',  # You should replace this with actual transaction ID
            amount=10.00,
            status='Completed'
        )
        # Update subscription end date
        profile = request.user.profile
        profile.extend_subscription(days=30)
        return redirect(reverse('payment_success'))
    return render(request, 'paypal_payment.html')

@login_required
def razorpay_payment(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.order.create({'amount': 10000, 'currency': 'INR', 'payment_capture': '1'})  # Adjusted amount to 10000 paise = 100 INR

    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            payment = Payment.objects.create(
                user=request.user,
                payment_method='razorpay',
                transaction_id=razorpay_payment_id,
                amount=100.00,  # Adjusted amount to match INR
                status='Completed'
            )
            # Update subscription end date
            profile = request.user.profile
            profile.extend_subscription(days=30)
            return redirect('payment_success')
        except razorpay.errors.SignatureVerificationError:
            return redirect('payment_failure')
    return render(request, 'razorpay_payment.html', {'payment': payment})



from django.shortcuts import render

def payment_success(request):
    return render(request, 'payment_success.html')

def payment_failure(request):
    return render(request, 'payment_failure.html')


@login_required
def prompt_payment(request):
    if request.method == 'POST':
        return redirect('payment_page')
    return render(request, 'prompt_payment.html')