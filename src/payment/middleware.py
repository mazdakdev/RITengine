from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

class PaymentRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # List of paths to exclude from payment check
        excluded_paths = [
            '/api/auth/me/',
            '/api/payment/checkout/',
            '/api/payment/webhook/stripe/',
        ]

        if request.path in excluded_paths:
            return None

        if self.payment_required(request):
            return JsonResponse({'detail': 'Payment required to continue.'}, status=402)

        return None

    def payment_required(self, request):
        return not request.user.is_trial_active and not request.user.has_active_subscription
