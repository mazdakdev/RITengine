import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from otp_twilio.models import TwilioSMSDevice
from django.core.validators import RegexValidator
from django.db import models
from datetime import timedelta
from django.conf import settings
from .providers import MeliPayamakProvider, get_sms_provider
from .services import SMSService

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        if not username:
            raise ValueError('The username field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

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

            service = OTPService(MeliPayamakProvider)

            code = service.send_otp(phone_number=self.number)

            self.token = str(code)
            self.valid_until = timezone.now() + timedelta(seconds=300)
            self.save()

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username_regex = RegexValidator(
        regex=r'^(?!\d)[^\@]*$',
        message="username must not start with numeric values nor contains @"
    )
    username = models.CharField(
            unique=True,
            max_length=15, 
            validators=[username_regex],
            error_messages={
                'unique': "This username is already taken. Please choose a different one.",
            }
         )
    email = models.EmailField(unique=True)
    f_name = models.CharField(max_length=50, blank=True, null=True)
    l_name = models.CharField(max_length=50, blank=True, null=True)
    inv_code = models.CharField(max_length=17, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to='users/')
    phone_number = PhoneNumberField(blank=True)
    username_change_count = models.IntegerField(default=0)

    is_email_verified = models.BooleanField(default=False)
    is_oauth_based = models.BooleanField(default=False)
    sms_device = models.OneToOneField(SMSDevice, null=True, blank=True, on_delete=models.SET_NULL)
    email_device = models.OneToOneField(EmailDevice, null=True, blank=True, on_delete=models.SET_NULL)
    totp_device = models.OneToOneField(TOTPDevice, null=True, blank=True, on_delete=models.SET_NULL)
    preferred_2fa = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('totp', 'TOTP'),
    ], null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def send_email(self, subject, message, from_email="from@example.com"):
        send_mail(
            subject,
            message,
            from_email,
            [self.email],
            fail_silently=False,
        )
    
    def send_sms(self, message):
        sms_service = OTPService(get_otp_provider(settings.SMS_PROVIDER))
        sms_service.send_message(self.phone_number, message)

class BackupCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True)
    is_used = models.BooleanField(default=False)
