from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice
# from django_twilio.models import TwilioSMSDevice
from django.utils import timezone
from rest_framework import serializers
import pyotp

User = get_user_model()

class CustomRegisterSerializer(RegisterSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "password",
        ]

    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        # a signal will be called to send the otp.
        return user


class CustomLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    otp = serializers.CharField(required=False, allow_blank=True) #for 2fa

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")
        otp = attrs.get("otp")

        if not identifier:
            raise serializers.ValidationError("Identifier must be set.")

        user = None

        try:
            user = User.objects.get(username=identifier)
            username = user.username
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this identifier.")

        if username:
            if not user.is_email_verified:
                user = authenticate(request=self.context.get("request"), username=username, password=password)
                if not user:
                    raise serializers.ValidationError("Invalid Credentials")

                # 2FA Verification
                preferred_2fa = user.preferred_2fa

                if preferred_2fa:
                    if not otp and user.preferred_2fa == "totp":  # OTP is required but not provided
                        raise serializers.ValidationError("2FA token is required for this user.")

                    elif preferred_2fa == 'email' and not otp:
                        raise serializers.ValidationError("2FA email otp is required for this user (you must request it).")

                    elif preferred_2fa == 'sms':
                        pass

                    elif preferred_2fa == 'totp':
                        device = TOTPDevice.objects.filter(user=user).first()

                    elif preferred_2fa == "email":
                        device = EmailDevice.objects.filter(user=user).first()

                    else:
                        device = None


                    if device and device.verify_token(otp):
                        attrs['user'] = user
                    else:
                        raise serializers.ValidationError("Invalid 2FA token.")
            raise serializers.ValidationError("User's E-mail is not yet verified")

        attrs['user'] = user
        return attrs

    def authenticate(self, **options):
       return super().authenticate(**options)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'email', 'username'] 

class OTPSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()

class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        otp = attrs.get('otp')

        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this identifier.")

        if not user.preferred_2fa:
            totp = pyotp.TOTP(user.otp_secret, interval=300)
            if totp.verify(otp):
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError("Invalid or expired OTP.")

        else:
            if user.preferred_2fa == "email":
                device = EmailDevice.objects.filter(user=user).first()

            elif user.preferred_2fa == "totp":
                device = TOTPDevice.objects.filter(user=user).first()

            elif user.preferred_2fa == "phone":
                pass

            if device and device.verify_token(otp):
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError("Invalid 2FA token.")

class PasswordChangeSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        otp = attrs.get('otp')
        new_password1 = attrs.get('new_password1')
        new_password2 = attrs.get('new_password2')

        if not otp:
            raise serializers.ValidationError("OTP is required.")

        if new_password1 != new_password2:
            raise serializers.ValidationError("New passwords do not match.")

        user = self.context['request'].user

        if not user.preferred_2fa:
            totp = pyotp.TOTP(user.otp_secret, interval=300)
            if totp.verify(otp):
                return attrs
            else:
                raise serializers.ValidationError("Invalid or expired OTP.")

        else:
            if user.preferred_2fa == "email":
                device = EmailDevice.objects.filter(user=user).first()

            elif user.preferred_2fa == "totp":
                device = TOTPDevice.objects.filter(user=user).first()

            elif user.preferred_2fa == "phone":
                pass

            if device and device.verify_token(otp):
               return attrs

            else:
                raise serializers.ValidationError("Invalid 2FA token.")



class Request2FASerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get("identifier")

        if not identifier:
            raise serializers.ValidationError("Identifier must be set.")

        else:

            try:
                user = User.objects.get(username=identifier)

            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=identifier)

                except User.DoesNotExist:
                    raise serializers.ValidationError("No user found with this identifier.")

            attrs["user"] = user
            return attrs

class Enable2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ('email', 'email'),
            ('totp', 'totp'),
            ('phone', 'phone'),
        ])


class Verify2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ('email', 'email'),
            ('totp', 'totp'),
            ('phone', 'phone'),
        ])
    otp = serializers.CharField(max_length=6)

#TODO: Reuse Duplicate Codes