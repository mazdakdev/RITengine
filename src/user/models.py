from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from phonenumber_field.modelfields import PhoneNumberField
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.db import models
from .tasks import send_email, send_text_email
from .otp_devices import SMSDevice, EmailDevice
from .validators import no_spaces_validator, username_regex
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractBaseUser, PermissionsMixin):

    username = models.CharField(
        unique=True,
        max_length=30,
        validators=[username_regex, no_spaces_validator],
        error_messages={
            "unique": "This username is already taken. Please choose a different one.",
        },
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    inv_code = models.CharField(max_length=17, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to="users/")
    phone_number = PhoneNumberField(blank=True)
    username_change_count = models.IntegerField(default=0)

    is_email_verified = models.BooleanField(default=False)
    is_oauth_based = models.BooleanField(default=False)
    sms_device = models.OneToOneField(
        SMSDevice, null=True, blank=True, on_delete=models.SET_NULL
    )
    email_device = models.OneToOneField(
        EmailDevice, null=True, blank=True, on_delete=models.SET_NULL
    )
    totp_device = models.OneToOneField(
        TOTPDevice, null=True, blank=True, on_delete=models.SET_NULL
    )
    preferred_2fa = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("sms", "SMS"),
            ("totp", "TOTP"),
        ],
        null=True,
        blank=True,
    )

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def send_email(self, subject, template_name, context={}, from_email=settings.EMAIL_FROM):
        send_email.delay(subject, template_name, self.email, context, from_email)

    def send_text_email(self, subject, message, from_email=settings.EMAIL_FROM):
        if settings.DEBUG:
            print(message)
        else:
            send_text_email.delay(subject, message, self.email, from_email)

    @property
    def is_trial_active(self):
        if not self.created_at:
            return False
        return timezone.now() < self.created_at + timedelta(days=settings.TRIAL_DAYS)

    # def send_sms(self, message):
    #     sms_service = SMSService(get_sms_provider(settings.SMS_PROVIDER))
    #     sms_service.send_message(self.phone_number, message)


class BackupCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True)
    is_used = models.BooleanField(default=False)
