from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
import pyotp

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

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username_regex = RegexValidator(
        regex=r'^(?!\d)[^\@]*$',
        message="username must not start with numeric values nor contains @"
    )
    username = models.CharField(unique=True, max_length=15, validators=[username_regex])
    email = models.EmailField(unique=True)
    f_name = models.CharField(max_length=50, blank=True, null=True)
    l_name = models.CharField(max_length=50, blank=True, null=True)
    inv_code = models.CharField(max_length=17, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    phone_number = PhoneNumberField(blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_otp_verified = models.BooleanField(default=False)
    otp_expiry_time = models.DateTimeField(blank=True, null=True)

    TWO_FA_CHOICES = [
        ('email_otp', 'Email OTP'),
        ('sms_otp', 'SMS OTP'),
        ('google_auth', 'Google Authenticator'),
    ]
    two_fa_method = models.CharField(max_length=20, choices=TWO_FA_CHOICES,blank=True, null=True)
    is_two_fa_enabled = models.BooleanField(default=False)
    totp_key = models.CharField(max_length=32, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def generate_otp(self):
        otp = pyotp.TOTP(pyotp.random_base32()).now()
        self.otp = otp
        print(otp)
        self.otp_expiry_time = timezone.now() + timedelta(minutes=30)
        self.save()

        return otp

    def send_email(self, subject, message):
        pass

    def send_sms(self, message):
        pass

