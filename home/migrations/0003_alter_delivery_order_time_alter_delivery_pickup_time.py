# Generated by Django 5.0.7 on 2024-11-11 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_alter_delivery_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='order_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='delivery',
            name='pickup_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]