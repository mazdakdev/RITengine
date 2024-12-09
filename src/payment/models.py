from django.db import models
from django.conf import settings
import stripe
from engine.models import EngineCategory
from rest_framework.exceptions import PermissionDenied
from project.models import Project

class Plan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    messages_limit = models.IntegerField()
    projects_limit = models.IntegerField()
    bookmarks_limit = models.IntegerField()
    engines_categories = models.ManyToManyField(EngineCategory)

    def __str__(self):
        return self.name

    def create_stripe_product(self):
        """
        Creates a product in Stripe when a Plan object is created.
        """
        if not self.stripe_product_id:
            product = stripe.Product.create(name=self.name)
            self.stripe_product_id = product.id
            self.save()

    def update_stripe_product(self):
        """
        Updates the product in Stripe when a Plan object is updated.
        """
        if self.stripe_product_id:
            stripe.Product.modify(
                self.stripe_product_id,
                name=self.name,
                description=self.description
            )

    def save(self, *args, **kwargs):
        if self.pk:
            self.update_stripe_product()
        else:
            self.create_stripe_product()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.stripe_product_id:
            stripe.Product.modify(self.stripe_product_id, active=False)
        super().delete(*args, **kwargs)


class PlanPrice(models.Model):
    plan = models.ForeignKey(Plan, related_name='prices', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval_count = models.IntegerField(default=1)  # E.g., every 1 month/year
    interval = models.CharField(
        max_length=20,
        choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')]
    )
    currency = models.CharField(
        max_length=5,
        choices=[
            ('usd', 'USD - United States Dollar'),
            ('eur', 'EUR - Euro'),
            ('gbp', 'GBP - British Pound'),
            ('chf', 'CHF - Swiss Franc'),
            ('aed', 'AED - UAE Dirham'),
        ]
    )
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.plan.name} - {self.interval_count} {self.interval} / {self.price} {self.currency}"

    def create_stripe_price(self):
        """
        Creates a price in Stripe for this plan and interval, including a trial period if specified.
        """
        if not self.stripe_price_id:
            price = stripe.Price.create(
                unit_amount=int(self.price * 100),  # smallest currency unit
                currency=self.currency,
                recurring={
                    "interval": self.interval,
                    "interval_count": self.interval_count
                },
                product=self.plan.stripe_product_id,

            )
            self.stripe_price_id = price.id
            self.save()


    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Modification of existing prices is not allowed (delete them).")
        else:
            self.create_stripe_price()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.stripe_price_id:
            stripe.Price.modify(self.stripe_price_id, active=False)
        super().delete(*args, **kwargs)


class Subscription(models.Model):
    customer = models.OneToOneField('Customer', on_delete=models.CASCADE, related_name='subscription')
    source_id = models.CharField(max_length=255)  # Stripe subscription ID
    plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=255, choices=[
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ], blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancel_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.customer.user.email} - {self.plan.name if self.plan else "Unknown Plan"}'

    def is_trialing(self):
        return self.status == 'trialing'

    def is_active(self):
        return self.status == 'active'

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer')
    source_id = models.CharField(max_length=255, blank=True, null=True)
    messages_sent_today = models.IntegerField(default=0)
    projects_created = models.IntegerField(default=0)
    bookmarks_created = models.IntegerField(default=0)

    def __str__(self):
        return self.user.email

    def get_current_limits(self):
        if self.has_active_subscription():
            plan_price = self.subscriptions.filter(status='active').last().plan_price
            plan = plan_price.plan
            return {
                'messages_limit': plan.messages_limit,
                'projects_limit': plan.projects_limit,
                'bookmarks_limit': plan.bookmarks_limit,
            }
        else:
            pass


    def has_active_subscription(self):
         """Check if the customer has an active or trialing subscription."""
         if hasattr(self, 'subscription'):
            return self.subscription.is_active() or self.subscription.is_trialing()
         return False

    def can_create_project(self):
        if not self.has_active_subscription():
            raise PermissionDenied("You must have an active subscription to create projects.")

        if self.subscription and self.projects_created >= self.subscription.plan.projects_limit:
            raise PermissionDenied("You have reached the maximum number of projects allowed by your subscription plan.")

    def create_project(self, **kwargs):
        self.can_create_project()
        project = Project.objects.create(user=self.user, **kwargs)
        self.projects_created += 1
        self.save()
        return project
