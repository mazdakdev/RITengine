from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
from django.core.validators import RegexValidator
from django.core.mail import send_mail
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

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


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

    is_email_verified = models.BooleanField(default=False)
    is_oauth_based = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    # twilio_device = models.OneToOneField(TwilioSMSDevice, null=True, blank=True, on_delete=models.SET_NULL)
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
    last_login = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def send_mail(self, subject, message):
        send_mail(
            subject,
            message,
            'from@example.com',
            [self.email],
            fail_silently=False,
        )

#TODO: Production: email

