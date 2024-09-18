from django.urls import path
from .views import CheckoutSessionView, StripeWebhookView

urlpatterns = [
    path('checkout/session/', CheckoutSessionView.as_view(), name='checkout'),
    path('checkout/webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
]
