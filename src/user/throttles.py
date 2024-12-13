from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import Throttled
from django.conf import settings
import os

class TwoFAAnonRateThrottle(AnonRateThrottle):
    rate = settings.TWO_FA_ANON_RATELIMIT

    def wait(self):
        wait_time = super().wait()
        if wait_time:
            raise Throttled(detail=f"Rate limit exceeded. Try again in {int(wait_time)} seconds.")
        return wait_time

class TwoFAUserRateThrottle(UserRateThrottle):
    rate = settings.TWO_FA_USER_RATELIMIT

    def wait(self):
        wait_time = super().wait()
        if wait_time:
            raise Throttled(detail=f"Rate limit exceeded. Try again in {int(wait_time)} seconds.")
        return wait_time
