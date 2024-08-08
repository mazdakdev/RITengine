from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
import os

class TwoFAAnonRateThrottle(AnonRateThrottle):
    rate = "5/min"

class TwoFAUserRateThrottle(UserRateThrottle):
    rate = "5/min"