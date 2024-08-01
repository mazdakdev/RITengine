from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.cache import cache
from RITengine.exceptions import CustomAPIException
from .exceptions import (
    EmailNotVerified, InvalidCredentials,
    InvalidTwoFaOrOtp, TwoFaRequired
)
from .utils import get_user_by_identifier, validate_two_fa, generate_2fa_challenge
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
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        tmp_token = attrs.get("tmp_token")
        otp = attrs.get("otp")

        user = get_user_by_identifier(identifier)

        if not user.is_email_verified:
            raise EmailNotVerified()

        if not user.preferred_2fa:
            raise CustomAPIException(
                detail="There is no two-factor setup for this user.",
                code="two_fa_not_set_up",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


        user_id = cache.get(f"2fa_{tmp_token}")

        if user_id is None or user_id != user.id:
            raise CustomAPIException(
                detail="Invalid or Expired temporary token",
                code="invalid_tmp_token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not validate_two_fa(user, otp):
            raise InvalidTwoFaOrOtp()

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"  #TODO


class CompleteRegisterSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        otp = attrs.get('otp')

        user = get_user_by_identifier(identifier)

        if not user.is_email_verified:
            raise EmailNotVerified()

        if not user.preferred_2fa:
            totp = pyotp.TOTP(user.otp_secret, interval=300)
            if totp.verify(otp):
                attrs['user'] = user
                return attrs
            else:
                raise InvalidTwoFaOrOtp()

        else:
            if not validate_two_fa(user, otp):
                raise InvalidTwoFaOrOtp()

        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        otp = attrs.get('otp')
        new_password1 = attrs.get('new_password1')
        new_password2 = attrs.get('new_password2')

        if not otp:
            raise TwoFaRequired()

        if new_password1 != new_password2:
            raise CustomAPIException(
                detail="New passwords do not match",
                code="passwords_do_not_match",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = self.context['request'].user

        if not user.preferred_2fa:
            totp = pyotp.TOTP(user.otp_secret, interval=300) #TODO: security check
            if totp.verify(otp):
                return attrs
            else:
                raise InvalidTwoFaOrOtp

        else:
            if not validate_two_fa(user, otp):
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
    otp = serializers.CharField(max_length=6)
