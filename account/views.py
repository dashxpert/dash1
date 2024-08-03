# account/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.core.mail import send_mail
from .forms import UserRegistrationForm, OTPVerificationForm, UserLoginForm
from dashboards.models import Profile
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Ensure profile exists before logging in
                try:
                    profile = user.profile
                    login(request, user)
                    return redirect('home')  # Redirect to your home page
                except Profile.DoesNotExist:
                    form.add_error(None, 'Profile does not exist for this user.')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')  # Redirect to your home page


from django.db import IntegrityError
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
import logging

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

                # Create profile and generate OTP
                profile, created = Profile.objects.get_or_create(user=user)

                if created:
                    profile.generate_otp()
                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is {profile.otp}',
                        'dashxpert6@gmail',  # Replace with your email
                        [user.email],
                        fail_silently=False,
                    )

                    # Store the user ID in the session
                    request.session['pending_user_id'] = user.id

                    return redirect('otp_verification')
                else:
                    form.add_error(None, 'A profile for this user already exists.')
            except IntegrityError as e:
                logger.error(f"IntegrityError: {e}")
                form.add_error(None, 'A user with this email already exists.')
            except Exception as e:
                logger.error(f"Unexpected error during registration: {e}", exc_info=True)
                form.add_error(None, 'An unexpected error occurred. Please try again.')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})



def verify_otp(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session.get('pending_user_id')

            if user_id:
                try:
                    profile = Profile.objects.get(user_id=user_id)
                    if profile.otp == otp and profile.otp_expiration > timezone.now():
                        # OTP is correct and not expired
                        user = profile.user
                        login(request, user)
                        del request.session['pending_user_id']
                        return redirect('thank_you')
                    form.add_error(None, 'Invalid OTP or OTP has expired.')
                except Profile.DoesNotExist:
                    form.add_error(None, 'Invalid user. Please register again.')
                except Exception as e:
                    logger.error(f"Unexpected error during OTP verification: {e}", exc_info=True)
                    form.add_error(None, 'An unexpected error occurred. Please try again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'users/verify_otp.html', {'form': form})

def thank_you(request):
    return render(request, 'users/thank_you.html')
