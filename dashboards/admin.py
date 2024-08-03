

# Register your models here.
# admin.py
from django.contrib import admin
from .models import UploadedFile, DashboardConfig
from .models import Profile

admin.site.register(UploadedFile)
admin.site.register(DashboardConfig)
admin.site.register(Profile)