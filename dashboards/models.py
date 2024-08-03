# models.py
import hashlib
from django.db import models
from django.contrib.auth.models import User

class DashboardConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    config = models.JSONField()  # Store configuration as JSON

# dashboards/models.py

from django.db import models
from django.contrib.auth.models import User
import random
from django.utils import timezone
import datetime
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    service_usage_count = models.PositiveIntegerField(default=0)
    subscription_start_date = models.DateTimeField(blank=True, null=True)
    subscription_end_date = models.DateTimeField(blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiration = models.DateTimeField(blank=True, null=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiration = timezone.now() + datetime.timedelta(minutes=10)
        self.save()

    def has_active_subscription(self):
        return self.subscription_end_date and self.subscription_end_date > timezone.now()

    def extend_subscription(self, days):
        if self.subscription_end_date and self.subscription_end_date > timezone.now():
            self.subscription_end_date += datetime.timedelta(days=days)
        else:
            self.subscription_end_date = timezone.now() + datetime.timedelta(days=days)
        self.save()

    def __str__(self):
        return self.user.username



    
class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
# models.py
import hashlib
from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    upload_date = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        if not self.file_hash:
            self.file_hash = self.generate_file_hash()
        super(Dataset, self).save(*args, **kwargs)

    def generate_file_hash(self):
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, null=True, blank=True)
    activity_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"

