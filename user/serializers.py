from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

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
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        if not username and not email:
            raise serializers.ValidationError("Either username or email must be set.")

        user = None

        if email:
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Email address or Password is invalid.")

        if username:
            user = authenticate(request=self.context.get("request"), username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid Credentials")

        if user and user_has_device(user):
            # User has 2FA enabled, require 2FA code
            if 'otp_code' not in attrs:
                raise serializers.ValidationError("You must provide a 2FA code to log in.")

            otp_code = attrs.get('otp_code')

            # Verify 2FA code
            totp_device = TOTPDevice.objects.get(user=user)
            totp = pyotp.TOTP(totp_device.config_url.split('=')[1])  # Extract secret key from config_url
            if not totp.verify(otp_code):
                raise serializers.ValidationError("Invalid 2FA code")

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

class TwoFAVerifySerializer(serializers.Serializer):
    code = serializers.IntegerField()

class TwoFASetupSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)
    google_auth_secret = serializers.CharField(read_only=True)
    method = serializers.ChoiceField(choices=['google_auth', 'sms', 'email'])


class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate_identifier(self, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this identifier.")
        
        self.context['user'] = user
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
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
        
        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        
        if timezone.now() > user.otp_expiry_time:
            raise serializers.ValidationError("OTP has expired.")

        attrs['user'] = user
        return attrs