from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
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

#TODO: encrypt OTP
#TODO: add phonenumber field
#TODO: add Image field
#TODO: username for OAUTH
#TODO: login through username *or email
