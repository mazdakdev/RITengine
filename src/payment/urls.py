from django.urls import path
from .views import CheckoutSessionView, StripeWebhookView, CustomerPortalView, PlanListView

urlpatterns = [
    path('checkout/session/', CheckoutSessionView.as_view(), name='checkout'),
    path('checkout/webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('plans/', PlanListView.as_view(), name='plans'),
    path('portal/', CustomerPortalView.as_view(), name='stripe_customer_portal'),
]
