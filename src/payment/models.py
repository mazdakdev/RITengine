from django.db import models
from django.conf import settings
import stripe

class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval_count = models.IntegerField(default=1)
    currency = models.CharField(
        max_length=5,
        choices = [
            ('usd', 'USD - United States Dollar'),
            ('eur', 'EUR - Euro'),
            ('gbp', 'GBP - British Pound'),
            ('chf', 'CHF - Swiss Franc'),
            ('aed', 'AED - UAE Dirham')
        ]
    )
    interval = models.CharField(
           max_length=20,
           choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')]
       )
    messages_per_day = models.IntegerField(default=0, help_text="Max messages allowed per day")
    projects_total = models.IntegerField(default=0, help_text="Max projects allowed for the subscription period")
    bookmarks_total = models.IntegerField(default=0, help_text="Max bookmarks allowed for the subscription period")
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.interval_count} {self.interval} / {self.price}"

    def create_stripe_plan(self):
        """
        Creates a plan in Stripe when a Plan object is created in Django.
        """
        product = stripe.Product.create(name=self.name)
        price = stripe.Price.create(
            unit_amount=int(self.price * 100),  # smallest currency unit
            currency=self.currency,
            recurring={
                "interval": self.interval,
                "interval_count": self.interval_count
            },
            product=product.id
        )
        self.stripe_price_id = price.id
        self.save()

    def save(self, *args, **kwargs):
        if not self.stripe_price_id:
            self.create_stripe_plan()
        super().save(*args, **kwargs)

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    source_id = models.CharField(max_length=255)
    messages_sent_today = models.IntegerField(default=0)
    projects_created = models.IntegerField(default=0)
    bookmarks_created = models.IntegerField(default=0)

    def __str__(self):
        return self.user.email

class Subscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='subscriptions')
    source_id = models.CharField(max_length=255)
    plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancel_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.customer.user.email} - {self.plan.name if self.plan else "Unknown Plan"}'
