from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime
import pyotp

def generate_otp():
    secret = pyotp.random_base32()
    otp = pyotp.TOTP(secret, interval=300)
    return otp, secret

def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    access_exp = datetime.utcfromtimestamp(access_token['exp']).replace(tzinfo=timezone.utc).isoformat()
    refresh_exp = datetime.utcfromtimestamp(refresh['exp']).replace(tzinfo=timezone.utc).isoformat()

    return refresh, access_token, access_exp, refresh_exp