from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from RITengine.exceptions import CustomAPIException
from . import exceptions
from phonenumber_field.serializerfields import PhoneNumberField
from .models import BackupCode
from rest_framework import serializers
from .utils.auth import (
        generate_2fa_challenge, generate_otp,
        validate_otp, validate_two_fa,
        send_otp_email
    )
from .utils.general import get_user_by_identifier

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']

    def validate(self, attrs):
        email = attrs.get('email')
        username = attrs.get('username')
        password1 = attrs.get('password1')
        password2 = attrs.get('password2')

        if password1 != password2:
            raise serializers.ValidationError("Passwords must match.")

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if not user.is_email_verified:
                return attrs
            else:
                raise serializers.ValidationError("Email is already registered.")

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if not user.is_email_verified:
                return attrs
            else:
                raise serializers.ValidationError("Username is already taken.")

        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        username = validated_data['username']
        password = validated_data['password1']

        user, created = User.objects.get_or_create(email=email, defaults={
            'username': username,
            'password': password,
        })

        if created:
            user.set_password(password)  # Hash the password before saving
            user.save()
            otp = generate_otp(user)
            send_otp_email(otp, user=user)

        else:
            if not user.is_email_verified:
                otp = generate_otp(user)
                send_otp_email(otp, user=user)
            else:
                raise serializers.ValidationError("User has already completed the registration process.")

        return user

class CompleteRegisterationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.InvalidCredentials()

        if user.is_email_verified:
            raise ValidationError("You don't need to complete your register.")

        if not validate_otp(user, otp):
            raise exceptions.InvalidTwoFaOrOtp()

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.is_email_verified = True
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = get_user_by_identifier(identifier)

        if not user:
            raise  exceptions.InvalidCredentials()

        username = user.username

        if not user.is_email_verified:
            raise exceptions.EmailNotVerified()

        authenticated_user = authenticate(
            request=self.context.get("request"), username=username, password=password
        )

        if not authenticated_user:
            raise exceptions.InvalidCredentials()

        attrs["user"] = authenticated_user
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
            raise exceptions.EmailNotVerified()

        if not user.preferred_2fa:
            raise exceptions.No2FASetUp()

        cached_tmp_token = cache.get(f"2fa_tmp_token_{user.id}")

        if tmp_token != cached_tmp_token:
            raise exceptions.InvalidTmpToken()

        if not validate_two_fa(user, code):
            # if not validate_backup_code(user, code):
            #     raise exceptions.InvalidTwoFaOrOtp()
            raise exceptions.InvalidTwoFaOrOtp()

        cache.delete(f"2fa_{user.id}")

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "image"]

        def __init__(self, *args, **kwargs):
            super(UserSerializer, self).__init__(*args, **kwargs)
            for field_name in self.fields:
                self.fields[field_name].read_only = True


class UserDetailsSerializer(serializers.ModelSerializer):
    username_change_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "username_change_count",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "inv_code",
            "birthday",
            "image",
            "preferred_2fa",
            "last_login",
        ]
        # extra_kwargs = {
        #     "first_name": {"required": True},
        #     "last_name": {"required": True},
        #     "birthday": {"required": True},
        # }
        read_only_fields = ["username", "email", "phone_number", "preferred_2fa", "last_login", "username_change_count"]

    def get_username_change_count(self, obj):
        return obj.username_change_count

class PasswordResetSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        user = get_user_by_identifier(identifier)

        if not user:
            raise exceptions.InvalidCredentials()

        if not user.is_email_verified:
            raise exceptions.EmailNotVerified()

        if not user.preferred_2fa:
            otp = generate_otp(user)
            send_otp_email(otp, user=user)

        else:
            generate_2fa_challenge(user)

        attrs["user"] = user
        return attrs


class CompletePasswordResetSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(style={"input_type": "password"})
    new_password2 = serializers.CharField(style={"input_type": "password"})
    identifier = serializers.CharField()
    tmp_token = serializers.CharField()
    code = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        new_password1 = attrs.get("new_password1")
        new_password2 = attrs.get("new_password2")
        code = attrs.get("code")
        tmp_token = attrs.get("tmp_token")

        # Validate new passwords match
        if new_password1 != new_password2:
            raise ValidationError("New passwords must match.")

        user = get_user_by_identifier(identifier)

        if not user:
            raise exceptions.InvalidCredentials()

        if not user.is_email_verified:
            raise CustomAPIException("Email is not verified.")

        cached_tmp_token = cache.get(f"passwd_tmp_token_{user.id}")
        if cached_tmp_token != tmp_token:
            raise exceptions.InvalidTmpToken()

        if not validate_otp(user, code) and not validate_two_fa(user, code):
            raise exceptions.InvalidTwoFaOrOtp()

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password1"]

        user.set_password(new_password)
        user.save()


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get("password")
        user = self.context.get("user")

        if not user.check_password(password):
            raise ValidationError("Your current password is incorrect.")

        if not user.preferred_2fa:
            otp = generate_otp(user)
            send_otp_email(otp, user=user)

        else:
            generate_2fa_challenge(user)

        return attrs

class CompletePasswordChangeSerializer(serializers.Serializer):
    code = serializers.CharField()
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password1 = attrs.get("new_password1")
        new_password2 = attrs.get("new_password2")
        code = attrs.get("code")
        user = self.context.get("user")

        if new_password1 != new_password2:
            raise ValidationError("New passwords do not match.")

        if not user.preferred_2fa:
            if not validate_otp(user, code):
                raise exceptions.InvalidTwoFaOrOtp()

        else:
            if not validate_two_fa(user, code):
                raise exceptions.InvalidTwoFaOrOtp()

        return attrs

    def save(self):
        user = self.context.get("user")
        new_password = self.validated_data.get("new_password1")
        user.set_password(new_password)
        user.save()
        return user



class Enable2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ("email", "email"),
            ("totp", "totp"),
            ("sms", "sms"),
        ]
    )


class Verify2FASerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ("email", "email"),
            ("totp", "totp"),
            ("sms", "sms"),
        ]
    )
    code = serializers.CharField(max_length=6)


class BackupCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupCode
        fields = ["code", "is_used"]


class UsernameChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

    def validate_username(self, value):
        user = self.context["request"].user

        if " " in value:
            raise serializers.ValidationError("Username must not contain spaces.")


        if user.username_change_count >= 3:
            raise CustomAPIException("You can't change your username more than 3 times.")
        return value

    def update(self, instance, validated_data):
        instance.username = validated_data['username']
        instance.username_change_count += 1
        instance.save()
        return instance


class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This e-mail address is already associated with another user.")
        return value


class CompleteEmailorPhoneChangeSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=10)

class PhoneChangeSerializer(serializers.Serializer):
    new_phone = PhoneNumberField()

    def validate_new_phone(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already associated with another user.")
        return value


class CompleteDisable2FASerializer(serializers.Serializer):
    code = serializers.CharField()

class Change2FAMethodSerializer(serializers.Serializer):
    new_method = serializers.ChoiceField(choices=["email", "sms", "totp"])

class CompleteChange2FAMethodSerializer(serializers.Serializer):
    new_method = serializers.ChoiceField(choices=["email", "sms", "totp"])
    code = serializers.CharField(min_length=6, max_length=10)

# TODO: adjust code max and min
# TODO: cleanese these
