# Generated by Django 5.0.6 on 2024-07-28 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0007_profile_otp_profile_otp_expiration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
