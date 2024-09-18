from django.db import models
from django.conf import settings

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    source_id = models.CharField(max_length=255)

    def __str__(self):
        return self.user.email

class Subscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='subscriptions')
    source_id = models.CharField(max_length=255)
    plan = models.CharField(max_length=255)
    currency = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.customer.user.email} - {self.plan}'
