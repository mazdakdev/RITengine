from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import Throttled
from django.utils.translation import gettext_lazy as _


class CustomAnonRateThrottle(AnonRateThrottle):
    def throttle_failure(self):
        wait_time = self.wait()
        raise CustomThrottled(wait_time=wait_time, detail='Rate limit exceeded.')

class CustomUserRateThrottle(UserRateThrottle):
    def throttle_failure(self):
        wait_time = self.wait()
        raise CustomThrottled(wait_time=wait_time, detail='Rate limit exceeded.')

class CustomThrottled(Throttled):
    def __init__(self, wait_time=None, detail=None):
        self.wait_time = wait_time
        self.detail = detail or _('Request was throttled.')
        self.status_code = 429