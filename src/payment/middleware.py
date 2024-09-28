from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

class PaymentRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        excluded_paths = [
            '/api/auth/me/',
            '/api/payment/checkout/session/',
            '/api/payment/checkout/webhook/',
            '/api/payment/portal/',
            '/api/auth/login/',
            '/api/payment/plans/',
        ]

        if request.path in excluded_paths:
            return None

        if not request.user.is_authenticated:
            return None

        if self.payment_required(request):
            return JsonResponse({'detail': 'Payment required to continue.'}, status=402)

        return None

    def payment_required(self, request):
        return request.user.is_trial_active
