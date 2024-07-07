from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from .utils import generate_random_numbers
from django.conf import settings
from django.db import models


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
        message="username mus't not start with numeric values nor contains @"
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

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def generate_otp(self):
        otp = generate_random_numbers()
        print(otp)  # DEBUG ONLY
        self.otp = otp
        self.otp_expiry_time = timezone.now() + timedelta(minutes=30)
        self.save()

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [self.email]
        send_mail("OTP CODE", str(otp), from_email, recipient_list)



#TODO: encrypt OTP
#TODO: TOTP
