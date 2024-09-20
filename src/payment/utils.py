from .models import Customer, Subscription
from datetime import datetime
from django.db import transaction
from .models import Plan
import stripe

@transaction.atomic
def handle_subscription_created(event):
    stripe_subscription = event['data']['object']
    customer = Customer.objects.get(source_id=stripe_subscription['customer'])
    price_id = stripe_subscription['items']['data'][0]['price']['id']
    plan = Plan.objects.filter(stripe_price_id=price_id).first()

    subscription, created = Subscription.objects.get_or_create(
        customer=customer,
        source_id=stripe_subscription['id'],
        defaults={
            'plan': plan,
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
    subscription.cancel_at_period_end = stripe_subscription['cancel_at_period_end']

    if stripe_subscription.get('canceled_at'):
        subscription.canceled_at = datetime.fromtimestamp(stripe_subscription['canceled_at'])
    if stripe_subscription.get('ended_at'):
        subscription.ended_at = datetime.fromtimestamp(stripe_subscription['ended_at'])

    if stripe_subscription.cancel_at:
        subscription.cancel_at = datetime.fromtimestamp(stripe_subscription['cancel_at'])

    subscription.save()
    return subscription
