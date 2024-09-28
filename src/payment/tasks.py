from celery import shared_task
from django.utils import timezone
from .models import Subscription

@shared_task
def reset_plan_limits():
    """
    Resets usage limits for each subscription's plan.
    This task should be scheduled to run daily or at a specified interval.
    """
    now = timezone.now()
    active_subscriptions = Subscription.objects.filter(status='active')

    for subscription in active_subscriptions:
        plan = subscription.plan
        customer = subscription.customer
        customer.messages_sent_today = 0
        customer.save()

    return f"Reset limits for {active_subscriptions.count()} active subscriptions"
