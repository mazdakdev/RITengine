import requests
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import BackupCode
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
from .providers import MeliPayamakProvider
import pyotp
import uuid
import random
import string

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

    access_exp = access_token['exp']
    refresh_exp = refresh['exp']

    access_exp_remaining = max(0, round(access_exp - current_time))
    refresh_exp_remaining = max(0, round(refresh_exp - current_time))

    return access_token, refresh, access_exp_remaining, refresh_exp_remaining

    
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
    device = getattr(user, f"{user.preferred_2fa}_device", None)

    if device and device.verify_token(otp):
        return True
    return False

def generate_2fa_challenge(user):
    method = user.preferred_2fa

    if method != "totp":
        device = getattr(user, f"{method}_device", None)

    device.generate_challenge()

def generate_tmp_token(user, scope):
    tmp_token = uuid.uuid4().hex
    cache.set(f'{scope}_tmp_token_{user.id}', tmp_token, timeout=300)

    return tmp_token

def generate_backup_codes(count=10, length=10):
    codes = []
    for _ in range(count):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        codes.append(code)
    return codes


def validate_backup_code(user, code):
     try:
        backup_code = get_object_or_404(BackupCode, user=user, code=code, is_used=False)
        backup_code.is_used = True
        backup_code.save()
        return True
     except BackupCode.DoesNotExist:
        return False