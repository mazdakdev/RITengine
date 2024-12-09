from celery import shared_task
from .models import Customer

@shared_task
def reset_plan_limits():
    """
    Resets usage limits for each subscription's plan.
    This task should be scheduled to run daily or at a specified interval.
    """

    active_customers = Customer.objects.filter(subscription__status__in=['active', 'trialing'])
    active_customers.update(messages_sent_today=0)

    return f"Reset limits for {active_customers.count()} active subscriptions"
