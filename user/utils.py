from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
import pyotp
import uuid

from user.models import SMSDevice

User = get_user_model()

def generate_otp():
    secret = pyotp.random_base32()
    otp = pyotp.TOTP(secret, interval=300)
    return otp, secret
    
def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    current_time = datetime.now(timezone.utc).timestamp()

    access_exp = round(access_token['exp'] - current_time)
    refresh_exp = round(refresh['exp'] - current_time)

    return access_token, refresh, access_exp, refresh_exp
    
def get_user_by_identifier(identifier: str):
    user = None
    identifier_choices = ["username", "email", "phone_number"]

    for attr in identifier_choices:
        try:
            user = User.objects.get(**{attr: identifier})
            break
        except User.DoesNotExist:
            continue

    return user

def validate_two_fa(user, otp):
    if user.preferred_2fa == "email":
        device = EmailDevice.objects.filter(user=user).first()
    elif user.preferred_2fa == "totp":
        device = TOTPDevice.objects.filter(user=user).first()
    elif user.preferred_2fa == "sms":
        device = SMSDevice.objects.filter(user=user).first()

    if device and device.verify_token(otp):
        return True

    return False

def generate_2fa_challenge(user: User):
    method = user.preferred_2fa

    if method == "email":
        device = EmailDevice.objects.filter(user=user).first()

    elif method == "sms":
        device = SMSDevice.objects.filter(user=user).first()

    device.generate_challenge()


def generate_tmp_token(user):
    tmp_token = uuid.uuid4().hex
    cache.set(f'2fa_{tmp_token}', user.id, timeout=300)

    return tmp_token