from typing import Optional, Union
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime
from user import exceptions
from RITengine.exceptions import CustomAPIException
from django_otp.conf import settings
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from user.models import SMSDevice, BackupCode
from django.contrib.auth import get_user_model
import pyotp
import uuid
import random
import string

User = get_user_model()

def generate_otp(user: User) -> str:
    """
    Generate an otp, cache its secret and return it.
    """
    secret = pyotp.random_base32()
    otp = pyotp.TOTP(secret, interval=300)
    cache.set(f"otp_secret_{user.id}", secret, timeout=300)
    return otp.now()

def validate_otp(user: User, otp: str) -> bool:
    """
    Validate the provided OTP for the given user.
    """
    try:
        otp_secret = cache.get(f"otp_secret_{user.id}")
        totp = pyotp.TOTP(otp_secret, interval=300)
    except Exception:
        raise exceptions.UnknownError()
    return totp.verify(otp)

def send_otp_email(otp: str, user: Optional[User] = None, recipient_email: Optional[str] = None) -> None:
    subject = "RITengine: OTP Verification"
    template_name = "emails/verification.html"

    if not user and not recipient_email:
        raise ValueError("Either a 'user' or 'recipient_email' must be provided.")

    context = {"token": otp}

    if user:
        user.send_email(
            subject=subject,
            template_name=template_name,
            context=context
        )

    elif recipient_email:
        html_message = render_to_string(template_name, context)
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.EMAIL_FROM,
            to=[recipient_email]
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

def validate_two_fa(user: User, otp: str) -> bool:
    """
    Validate the provided 2FA code for the given user.
    """
    device = getattr(user, f"{user.preferred_2fa}_device", None)
    return device and device.verify_token(otp)

def generate_2fa_challenge(user: User) -> None:
    """
    If user 2FA method is E-mail or SMS, Sends 2FA code to the user.
    """
    method = user.preferred_2fa

    if method != "totp":
        device = getattr(user, f"{method}_device", None)
        if device:
            device.generate_challenge()

def generate_tmp_token(user: User, scope: str) -> str:
    """
    Generate a temporary token for the given user.
    purpose: proof of completion of the init step
    """
    tmp_token = uuid.uuid4().hex
    cache.set(f"{scope}_tmp_token_{user.id}", tmp_token, timeout=300)

    return tmp_token

def generate_backup_codes(count: int = 10, length: int = 10) -> list[str]:
    codes = []
    for _ in range(count):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        codes.append(code)
    return codes

def validate_backup_code(user: User, code: str) -> bool:
    try:
        backup_code = get_object_or_404(BackupCode, user=user, code=code, is_used=False)
        backup_code.is_used = True
        backup_code.save()
        return True
    except BackupCode.DoesNotExist:
        return False

def create_2fa_device(user: User, method: str) -> Union[EmailDevice, SMSDevice, TOTPDevice]:
    if method == "email":
        return EmailDevice(user=user, confirmed=False)
    elif method == "sms":
        if not user.phone_number:
            raise CustomAPIException("You have not set any phone number.")
        return SMSDevice(user=user, number=user.phone_number, confirmed=False)
    elif method == "totp":
        return TOTPDevice(user=user, step=60, confirmed=False)
    else:
        raise CustomAPIException("Invalid 2FA method.")

def remove_existing_2fa_devices(user: User, exclude_method: str = "") -> None:
    for method in ['email', 'sms', 'totp']:
        if method == exclude_method:
            continue
        device = getattr(user, f"{method}_device", None)
        if device:
            device.delete()
            setattr(user, f"{method}_device", None)
            user.save()

def get_jwt_token(user: User) -> tuple[RefreshToken, RefreshToken, int, int]:
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    current_time = datetime.now(timezone.utc).timestamp()

    access_exp = access_token.get("exp", current_time)  # using current_time as a fallback
    refresh_exp = refresh.get("exp", current_time)

    access_exp_remaining = max(0, round(access_exp - current_time))
    refresh_exp_remaining = max(0, round(refresh_exp - current_time))

    return access_token, refresh, access_exp_remaining, refresh_exp_remaining
