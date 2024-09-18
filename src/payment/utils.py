from .models import Customer, Subscription
from datetime import datetime
from django.db import transaction

@transaction.atomic
def handle_subscription_created(event):
    stripe_subscription = event['data']['object']
    customer = Customer.objects.get(source_id=stripe_subscription['customer'])

    subscription, created = Subscription.objects.get_or_create(
        customer=customer,
        source_id=stripe_subscription['id'],
        defaults={
            'status': stripe_subscription['status'],
            'currency': stripe_subscription['currency'],
            'amount': stripe_subscription['plan']['amount'] / 100,
            'started_at': datetime.fromtimestamp(stripe_subscription['created']),
        }
    )

    return subscription

@transaction.atomic
def handle_subscription_updated(event):
    stripe_subscription = event['data']['object']
    subscription = Subscription.objects.get(source_id=stripe_subscription['id'])

    subscription.status = stripe_subscription['status']
    if stripe_subscription.get('canceled_at'):
        subscription.canceled_at = datetime.fromtimestamp(stripe_subscription['canceled_at'])
    if stripe_subscription.get('ended_at'):
        subscription.ended_at = datetime.fromtimestamp(stripe_subscription['ended_at'])

    subscription.save()
    return subscription
