from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import Throttled
import os

class TwoFAAnonRateThrottle(AnonRateThrottle):
    rate = "10/min"

    def wait(self):
        wait_time = super().wait()
        if wait_time:
            raise Throttled(detail=f"Rate limit exceeded. Try again in {int(wait_time)} seconds.")
        return wait_time

class TwoFAUserRateThrottle(UserRateThrottle):
    rate = "10/min"

    def wait(self):
        wait_time = super().wait()
        if wait_time:
            raise Throttled(detail=f"Rate limit exceeded. Try again in {int(wait_time)} seconds.")
        return wait_time