from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

class PaymentRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        excluded_prefixes = [
            '/api/payment/checkout/session/',
            '/api/payment/checkout/webhook/',
            '/api/payment/portal/',
            '/api/auth/login/',
            '/api/payment/plans/',
            '/api/auth/me/',
            '/admin/',
        ]

        if any(request.path.startswith(prefix) for prefix in excluded_prefixes):
            return None

        if not request.user.is_authenticated:
            return None

        if self.payment_required(request):
            return JsonResponse({'detail': 'Payment required to continue.'}, status=402)

        return None

    def payment_required(self, request):
        return request.user.is_trial_active
