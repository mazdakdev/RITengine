from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import BackupCode
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from . import exceptions
from django.db.models import Count, F
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.timezone import now
from RITengine.exceptions import CustomAPIException
from django_otp.conf import settings
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from .models import SMSDevice
from datetime import timedelta
import json
import pyotp
import uuid
import random
import string

User = get_user_model()


def generate_otp(user):
    """
    Generate an otp, cache its secret and return it.
    """
    secret = pyotp.random_base32()
    otp = pyotp.TOTP(secret, interval=300)
    cache.set(f"otp_secret_{user.id}", secret, timeout=300)

    return otp.now()

def send_otp_email(otp, user=None, recipient_email=None, subject="RITengine: OTP Verification", template_name="emails/verification.html"):
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

def verify_otp(user, otp):
    try:
        otp_secret = cache.get(f"otp_secret_{user.id}")
        totp = pyotp.TOTP(otp_secret, interval=300)
    except Exception:
        raise exceptions.UnknownError()

    if not totp.verify(otp):
        return False
    return True

def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    current_time = datetime.now(timezone.utc).timestamp()

    access_exp = access_token.get("exp", current_time) #using current_time as a fallback
    refresh_exp = refresh.get("exp", current_time)

    access_exp_remaining = max(0, round(access_exp - current_time))
    refresh_exp_remaining = max(0, round(refresh_exp - current_time))

    return access_token, refresh, access_exp_remaining, refresh_exp_remaining


def get_user_by_identifier(identifier: str):
    """
      Fetch a user by either username, email, or phone number/
    """
    try:
        user = User.objects.get(
            Q(username=identifier) | Q(email=identifier) | Q(phone_number=identifier)
        )
        return user
    except User.DoesNotExist:
        raise exceptions.InvalidCredentials()

def validate_two_fa(user, otp):
    device = getattr(user, f"{user.preferred_2fa}_device", None)

    if device and device.verify_token(otp):
        return True
    return False


def generate_2fa_challenge(user):
    """
    If user 2FA method is E-mail or SMS, Sends 2FA code to the user.
    """
    method = user.preferred_2fa

    if method != "totp":
        device = getattr(user, f"{method}_device", None)
        device.generate_challenge()


def generate_tmp_token(user, scope):
    tmp_token = uuid.uuid4().hex
    cache.set(f"{scope}_tmp_token_{user.id}", tmp_token, timeout=300)

    return tmp_token


def generate_backup_codes(count=10, length=10):
    codes = []
    for _ in range(count):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
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


def validate_otp(user, otp):
    otp_secret = cache.get(f"otp_secret_{user.id}")\

    if otp_secret is not None:
        totp = pyotp.TOTP(otp_secret, interval=300)
        if not totp.verify(otp):
           return False
        return True


def get_user_stats():
    """
    Retrieve and annotate user statistics for various charts.
    """
    # User Registration Trends
    registrations_by_month = User.objects.annotate(
        year=ExtractYear('created_at'),
        month=ExtractMonth('created_at')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    registration_data = {
        'labels': [f"{entry['month']}/{entry['year']}" for entry in registrations_by_month],
        'datasets': [{
            'label': 'User Registrations',
            'data': [entry['count'] for entry in registrations_by_month],
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
        }]
    }

    # User Activity
    start_date = now() - timedelta(days=30)
    activity_by_day = User.objects.filter(last_login__gte=start_date).annotate(
        date=F('last_login__date')
    ).values('date').annotate(count=Count('id')).order_by('date')

    activity_data = {
        'labels': [entry['date'].strftime('%Y-%m-%d') for entry in activity_by_day],
        'datasets': [{
            'label': 'User Activity',
            'data': [entry['count'] for entry in activity_by_day],
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1,
        }]
    }

    # User Status
    user_status = User.objects.values('is_active').annotate(count=Count('id'))

    status_data = {
        'labels': ['Active', 'Inactive'],
        'datasets': [{
            'label': 'User Status',
            'data': [entry['count'] for entry in user_status],
            'backgroundColor': ['rgba(75, 192, 192, 0.2)', 'rgba(255, 99, 132, 0.2)'],
            'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
            'borderWidth': 1,
        }]
    }

    # User Login Frequency
    login_frequency_by_month = User.objects.filter(last_login__gte=start_date).annotate(
        year=ExtractYear('last_login'),
        month=ExtractMonth('last_login')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    login_frequency_data = {
        'labels': [f"{entry['month']}/{entry['year']}" for entry in login_frequency_by_month],
        'datasets': [{
            'label': 'User Login Frequency',
            'data': [entry['count'] for entry in login_frequency_by_month],
            'backgroundColor': 'rgba(255, 159, 64, 0.2)',
            'borderColor': 'rgba(255, 159, 64, 1)',
            'borderWidth': 1,
        }]
    }

    # Combine all data
    return {
        'registration_data': registration_data,
        'activity_data': activity_data,
        'status_data': status_data,
        'login_frequency_data': login_frequency_data,
    }


def create_2fa_device(user, method):
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


def remove_existing_2fa_devices(user, exclude_method=""):
    for method in ['email', 'sms', 'totp']:
        if method == exclude_method:
            continue

        device = getattr(user, f"{method}_device", None)
        if device:
            device.delete()
            setattr(user, f"{method}_device", None)
            user.save()
