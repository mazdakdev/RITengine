from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from .managers import UserManager
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from django.template.loader import render_to_string
from otp_twilio.models import TwilioSMSDevice
from django.core.validators import RegexValidator
from django.db import models
from datetime import timedelta
from .providers import MeliPayamakProvider
from .services import SMSService

class SMSDevice(TwilioSMSDevice):
    class Meta:
        proxy = True

    def generate_challenge(self):
        if settings.SMS_PROVIDER == "twilio":
            super().generate_challenge(self)

        elif settings.SMS_PROVIDER == "melipayamak":
            """
                Provider itself generates the challenge and delivers it.
            """

            service = SMSService(MeliPayamakProvider)

            code = service.send_otp(phone_number=self.number)

            self.token = str(code)
            self.valid_until = timezone.now() + timedelta(seconds=300)
            self.save()


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username_regex = RegexValidator(
        regex=r"^(?!\d)[^\@]*$",
        message="username must not start with numeric values nor contains @",
    )
    username = models.CharField(
        unique=True,
        max_length=15,
        validators=[username_regex],
        error_messages={
            "unique": "This username is already taken. Please choose a different one.",
        },
    )
    email = models.EmailField(unique=True)
    f_name = models.CharField(max_length=50, blank=True, null=True)
    l_name = models.CharField(max_length=50, blank=True, null=True)
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
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def send_email(self, subject, template_name, context, from_email=settings.EMAIL_FROM):
        """
        Send an email using an HTML template.

        :param subject: Subject of the email
        :param template_name: Path to the HTML template
        :param context: Context data to render the template with
        :param from_email: Sender email address
        """

        html_message = render_to_string(template_name, context)

        email = EmailMessage(
            subject,
            html_message,
            from_email,
            [self.email]
        )

        email.content_subtype = "html"
        email.send(fail_silently=False)

    # def send_sms(self, message):
    #     sms_service = SMSService(get_sms_provider(settings.SMS_PROVIDER))
    #     sms_service.send_message(self.phone_number, message)


class BackupCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True)
    is_used = models.BooleanField(default=False)
