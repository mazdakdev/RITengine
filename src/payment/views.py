from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from .serializers import SubscriptionSerializer
import stripe
from django.contrib.auth import get_user_model

User = get_user_model()

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            price_id = serializer.get_price_id()

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                success_url=f"https://{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"https://{settings.FRONTEND_URL}/cancel/",
                metadata={
                    'user_id': request.user.id,
                }
            )

            return Response({'url': checkout_session.url})
        return Response(serializer.errors, status=400)

class StripeWebhookView(APIView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({'error': str(e)}, status=400)

        event_type = event['type']
        data = event['data']['object']
        user_id = data.get('metadata', {}).get('user_id')

        if not user_id:
            return JsonResponse({'status': 'user_id missing'}, status=400)

        user = User.objects.filter(id=user_id).first()

        if user is None:
            return JsonResponse({'status': 'user not found'}, status=404)

        if event_type == 'invoice.paid':
            user.has_active_subscription = True
            user.stripeSubscriptionId = data['subscription']
            user.save()

        elif event_type == 'invoice.payment_failed':
            user.has_active_subscription = False
            user.save()

        elif event_type == 'customer.subscription.deleted':
            user.has_active_subscription = False
            user.save()

        return JsonResponse({'status': 'success'}, status=200)
