# Generated by Django 5.0.2 on 2025-04-24 21:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prescriptions', '0002_prescription_expiry_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prescription',
            name='expiry_date',
            field=models.DateField(default=datetime.date(2024, 1, 1)),
        ),
    ]
