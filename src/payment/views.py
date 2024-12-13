from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from .serializers import SubscriptionSerializer
from django.views.decorators.csrf import csrf_exempt
from .models import Customer
from RITengine.exceptions import CustomAPIException
from django.http import JsonResponse
from .utils import handle_subscription_created, handle_subscription_updated
import stripe
from .models import Plan
from django.contrib.auth import get_user_model
from .serializers import PlanSerializer


class CheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        price_id = serializer.get_price_id()
        user = request.user

        try:
            customer, created = Customer.objects.get_or_create(user=user, defaults={
                'source_id': stripe.Customer.create(email=user.email).id
            })


            if customer.has_active_subscription():
                raise CustomAPIException("You already have an active subscription.")

            session = stripe.checkout.Session.create(
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=f'https://{settings.FRONTEND_URL}/checkout/success',
                cancel_url=f'https://{settings.FRONTEND_URL}/checkout/cancel',
                automatic_tax={'enabled': True},
                customer=customer.source_id,
                customer_update={'address': 'auto'},
                subscription_data={
                    'trial_period_days': settings.TRIAL_DAYS,
                    'trial_settings': {
                        'end_behavior': {
                            'missing_payment_method': 'cancel'
                        }
                    }
                },
                payment_method_collection='if_required'
            )

            return Response({'url': session.url}, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StripeWebhookView(APIView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            return JsonResponse({'error': str(e)}, status=400)

        event_type = event['type']
        if event_type == 'customer.subscription.created':
            handle_subscription_created(event)
        elif event_type in ['customer.subscription.updated', 'customer.subscription.deleted']:
            handle_subscription_updated(event)

        return Response(status=status.HTTP_200_OK)

class CustomerPortalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
               session = stripe.billing_portal.Session.create(
                   customer=request.user.customer.source_id,
                   return_url="http://"+settings.FRONTEND_URL + '/subscriptions',
               )
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        return Response({'url': session.url}, status=201)


class PlanListView(APIView):
    def get(self, request):
        plans = Plan.objects.all()

        categorized_plans = {
            'daily': [],
            'weekly': [],
            'monthly': [],
            'yearly': []
        }

        for plan in plans:
            for price in plan.prices.all():
                serialized_plan = PlanSerializer(plan).data
                serialized_price = {
                    'id': price.id,
                    'price': str(price.price),
                    'interval_count': price.interval_count,
                    'interval': price.interval,
                    'currency': price.currency
                }

                serialized_plan['prices'] = [serialized_price]

                if price.interval == 'day':
                    categorized_plans['daily'].append(serialized_plan)
                elif price.interval == 'week':
                    categorized_plans['weekly'].append(serialized_plan)
                elif price.interval == 'month':
                    categorized_plans['monthly'].append(serialized_plan)
                elif price.interval == 'year':
                    categorized_plans['yearly'].append(serialized_plan)

        return Response(categorized_plans)
