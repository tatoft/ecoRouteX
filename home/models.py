from django.db import models

class Delivery(models.Model):
    order_id = models.CharField(max_length=50)
    agent_age = models.IntegerField()
    agent_rating = models.FloatField(null=True, blank=True)
    store_latitude = models.FloatField()
    store_longitude = models.FloatField()
    drop_latitude = models.FloatField()
    drop_longitude = models.FloatField()
    order_date = models.DateField()
    order_time = models.TimeField(null=True, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)
    weather = models.CharField(max_length=50, null=True, blank=True)
    traffic = models.CharField(max_length=50)
    vehicle = models.CharField(max_length=50)
    area = models.CharField(max_length=50)
    delivery_time = models.IntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.order_id} - {self.category}"

