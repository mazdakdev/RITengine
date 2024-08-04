from rest_framework.throttling import AnonRateThrottle
import os

class TwoFAAnonRateThrottle(AnonRateThrottle):
    rate = os.getenv("TwoFaRateLimit")
