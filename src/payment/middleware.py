from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

class PaymentRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        excluded_prefixes = [
            '/api/payment/checkout/session/',
            '/api/payment/checkout/webhook/',
            '/api/payment/portal/',
            '/api/auth/login/',
            '/api/legal/',
            '/api/payment/plans/',
            '/api/auth/me/',
            '/admin/',
        ]

        if any(request.path.startswith(prefix) for prefix in excluded_prefixes):
            return None

        if request.user.is_superuser or request.user.is_staff:
            return None

        if not request.user.is_authenticated:
            return None

        customer = getattr(request.user, 'customer', None)
        if not customer or not customer.has_active_subscription():
            return JsonResponse({'detail': 'Payment required to continue.'}, status=402)

        return None
