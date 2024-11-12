# Generated by Django 5.0.7 on 2024-11-11 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=20, unique=True)),
                ('agent_age', models.IntegerField()),
                ('agent_rating', models.FloatField(blank=True, null=True)),
                ('store_latitude', models.FloatField()),
                ('store_longitude', models.FloatField()),
                ('drop_latitude', models.FloatField()),
                ('drop_longitude', models.FloatField()),
                ('order_date', models.DateField()),
                ('order_time', models.TimeField()),
                ('pickup_time', models.TimeField()),
                ('weather', models.CharField(blank=True, max_length=50, null=True)),
                ('traffic', models.CharField(max_length=20)),
                ('vehicle', models.CharField(max_length=20)),
                ('area', models.CharField(max_length=50)),
                ('delivery_time', models.IntegerField()),
                ('category', models.CharField(max_length=50)),
            ],
        ),
    ]