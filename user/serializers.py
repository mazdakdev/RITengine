from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError, APIException

from RITengine.exceptions import CustomAPIException
from .exceptions import (
    EmailNotVerified, InvalidCredentials,
    InvalidTwoFaOrOtp, TwoFaRequired
)
from .utils import get_user_by_identifier, validate_two_fa, validate_backup_code
from .models import BackupCode
from rest_framework import serializers, status
import pyotp

User = get_user_model()

class CustomRegisterSerializer(RegisterSerializer):
    def validate_email(self, email):
        email = get_adapter().clean_email(email)

        if email and User.objects.filter(email=email):
            raise serializers.ValidationError(
                'A user is already registered with this e-mail address.',
            )
        return email

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = get_user_by_identifier(identifier)


        if user is None:
            raise InvalidCredentials()

        username = user.username

        if not user.is_email_verified:
            raise EmailNotVerified()

        authenticated_user = authenticate(request=self.context.get("request"), username=username, password=password)

        if not authenticated_user:
            raise InvalidCredentials()

        attrs['user'] = authenticated_user
        return attrs

class CompleteLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    tmp_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=10)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        tmp_token = attrs.get("tmp_token")
        code = attrs.get("code")

        user = get_user_by_identifier(identifier)

        if not user.is_email_verified:
            raise EmailNotVerified()

        if not user.preferred_2fa:
            raise CustomAPIException(
                detail="There is no two-factor setup for this user.",
                code="two_fa_not_set_up",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        tmp_token = cache.get(f"2fa_tmp_token_{user.id}")

        if tmp_token is None:
            raise CustomAPIException(
                detail="Invalid or Expired temporary token",
                code="invalid_tmp_token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not validate_two_fa(user, code):
            if not validate_backup_code(user, code):
                raise InvalidTwoFaOrOtp()
            raise InvalidTwoFaOrOtp()

        cache.delete(f"2fa_{user.id}")

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "f_name", "l_name"]

        def __init__(self, *args, **kwargs):
            super(UserSerializer, self).__init__(*args, **kwargs)
            for field_name in self.fields:
                self.fields[field_name].read_only = True

class UserDetailsSerializer(serializers.ModelSerializer):
    inv_code = serializers.CharField(min_length=16, max_length=17)

    class Meta:
        model = User
        fields = [
                "username", "email", "f_name", 
                "l_name", "phone_number", "inv_code",
                "birthday", "image", "last_login"
        ]
        extra_kwargs = {
            'f_name': {'required': True},
            'l_name': {'required': True},
            'birthday': {'required': True},

        }
        read_only_fields = ["username", "email", "phone_number", "last_login"]



class CompleteRegisterSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        code = attrs.get('code')

        user = get_user_by_identifier(identifier)

        if not user.is_email_verified:
            raise EmailNotVerified()

        if not user.preferred_2fa:
            otp_secret = cache.get(f"otp_secret_{user.id}")
            totp = pyotp.TOTP(otp_secret, interval=300)
            if totp.verify(code):
                attrs['user'] = user
                return attrs
            else:
                raise InvalidTwoFaOrOtp()

        else:
            if not validate_two_fa(user, code):
                raise InvalidTwoFaOrOtp()

        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        code = attrs.get('code')
        new_password1 = attrs.get('new_password1')
        new_password2 = attrs.get('new_password2')

        if not code:
            raise TwoFaRequired()

        if new_password1 != new_password2:
            raise CustomAPIException(
                detail="New passwords do not match",
                code="passwords_do_not_match",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = self.context['request'].user

        if not user.preferred_2fa:
            otp_secret = cache.get(f"otp_secret{user.id}")
            totp = pyotp.TOTP(otp_secret, interval=300) #TODO: security check
            if totp.verify(code):
                return attrs
            else:
                raise InvalidTwoFaOrOtp

        else:
            if not validate_two_fa(user, code):
                raise InvalidTwoFaOrOtp
            return attrs

class Request2FASerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        user = get_user_by_identifier(identifier)
        if user is None:
            raise InvalidCredentials()

        attrs["user"] = user
        return attrs


class Enable2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ('email', 'email'),
            ('totp', 'totp'),
            ('sms', 'sms'),
        ])


class Verify2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ('email', 'email'),
            ('totp', 'totp'),
            ('sms', 'sms'),
        ])
    code = serializers.CharField(max_length=6)

class BackupCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupCode
        fields = ['code', 'is_used']


class UsernameChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

    def validate(self, attrs):
        user = self.context['request'].user

        if user.username_change_count >= 3:
            raise APIException("You can't change your username more than 3 times.")

        return super().validate(attrs)

class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

class CompleteEmailChangeSerializer(serializers.Serializer):
    tmp_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=10)
 