from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from .models import BackupCode
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from .utils import auth as auth_utils
from .utils import general as general_utils
from .permissions import IsNotOAuthUser, CanChangeEmail, CanChangePhone
from RITengine.exceptions import CustomAPIException
from . import exceptions
from .serializers import (
    Verify2FASerializer, Enable2FASerializer,
    PasswordChangeSerializer, PasswordResetSerializer, LoginSerializer,
    CompleteRegisterationSerializer, UsernameChangeSerializer, UserSerializer,
    CompleteLoginSerializer, RegistrationSerializer, UserDetailsSerializer,
    BackupCodeSerializer, EmailChangeSerializer, CompleteEmailorPhoneChangeSerializer,
    PhoneChangeSerializer, CompleteDisable2FASerializer, CompletePasswordChangeSerializer,
    CompletePasswordResetSerializer, Change2FAMethodSerializer, CompleteChange2FAMethodSerializer
)
from .throttles import TwoFAAnonRateThrottle, TwoFAUserRateThrottle
from rest_framework import generics
from django.db.models import Q
from .tasks import send_sms_otp_task

User = get_user_model()

class GitHubLoginView(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = f"{settings.OAUTH_BASE_CALLBACK_URL}/github"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
        self.request.user.save()

    def get_response(self):
        user = self.request.user
        serializer = UserSerializer(user)
        access, refresh, access_exp, refresh_exp = auth_utils.get_jwt_token(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = f"{settings.OAUTH_BASE_CALLBACK_URL}/google"
    client_class = OAuth2Client

    def process_login(self):
        super().process_login()
        self.request.user.is_email_verified = True
        self.request.user.is_oauth_based = True
        self.request.user.save()

    def get_response(self):
        user = self.request.user
        serializer = UserSerializer(user)
        access, refresh, access_exp, refresh_exp = auth_utils.get_jwt_token(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CustomRegisterView(APIView):
    """
    Creates user obj and sends an otp
    """
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request)

        return Response(
            {"status": "success", "detail": "Verification code sent successfully."},
            status=status.HTTP_200_OK,
        )

class CompleteRegistrationView(APIView):
    """
    Verifies the otp and hence the user's registertaion
    """
    def post(self, request):
        serializer = CompleteRegisterationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.send_email(
                subject=f"Welcome to RITengine",
                template_name="emails/welcome.html",
            )

        access, refresh, access_exp, refresh_exp = auth_utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                # 'status': "success",
                # 'data': {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
                # }
            },
            status=status.HTTP_200_OK,
        )


class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if user.preferred_2fa:
            tmp_token = auth_utils.generate_tmp_token(user, "2fa")
            auth_utils.generate_2fa_challenge(user)

            return Response(
                {"status": "2fa_required", "tmp_token": tmp_token},
                status=status.HTTP_202_ACCEPTED,
            )

        user.last_login = timezone.now()
        user.save()
        access, refresh, access_exp, refresh_exp = auth_utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CompleteLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CompleteLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user.last_login = timezone.now()
        user.save()
        access, refresh, access_exp, refresh_exp = auth_utils.get_jwt_token(user)
        user_serializer = UserSerializer(user)

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "access_expiration": access_exp,
                "refresh_expiration": refresh_exp,
                "user": user_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class UserDetailsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailsSerializer

    def get_object(self):
        return self.request.user

    # def partial_update(self, request, *args, **kwargs):
    #     required_fields = ["first_name", "last_name", "birthday"]

    #     current_data = self.get_object()
    #     serializer = self.get_serializer(data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)

    #     for field in required_fields:
    #         if (
    #             field not in serializer.validated_data
    #             and getattr(current_data, field) is None
    #         ):
    #             # Required field is missing
    #             return Response(
    #                 {
    #                     "status": "error",
    #                     "details": f"The field {field} is required to be updated first.",
    #                     "error_code": "required_field_missing",
    #                 },
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )

    #     user = self.get_object()
    #     serializer = self.get_serializer(user, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)

    #     return Response(serializer.data)


class PasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser,]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate temporary token and bind it to the user ID
        tmp_token = auth_utils.generate_tmp_token(user, "passwd")

        return Response(
            {
                "status": "verification_required",
                "tmp_token": tmp_token
            },
            status=status.HTTP_202_ACCEPTED,
        )

class CompletePasswordResetView(APIView):
    permission_classes = [IsNotOAuthUser,]

    def post(self, request):
        serializer = CompletePasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"status": "success", "message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"status": "verification_required",},
            status=status.HTTP_202_ACCEPTED,
        )

class CompletePasswordChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]

    def post(self , request, *args, **kwargs):
        serializer = CompletePasswordChangeSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "status": "success",
                "detail":"Password changed successfully"
            },
            status=status.HTTP_200_OK,
        )

class Enable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request):
        user = request.user
        serializer = Enable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]

        if user.preferred_2fa:
            return Response(
                {"status": "error", "detail": "2FA is already enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_utils.remove_existing_2fa_devices(user)
        user.preferred_2fa = None
        user.save()

        device = auth_utils.create_2fa_device(user, method)
        device.save()
        setattr(user, f"{method}_device", device)
        user.save()

        response_data = {"status": "success"}
        if method in ["email", "sms"]:
            device.generate_challenge()
            response_data["detail"] = "An email has been sent." if method == "email" else "An SMS has been sent."
        else:
            response_data["provisioning_uri"] = device.config_url

        return Response(response_data, status=status.HTTP_200_OK)


class Verify2FASetupView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        code = serializer.validated_data["code"]
        user = request.user

        device = getattr(user, f"{method}_device", None)

        if device and device.verify_token(code):
            device.confirmed = True
            device.save()
            user.preferred_2fa = method
            user.save()

            # Generate backup codes
            codes = auth_utils.generate_backup_codes()
            backup_codes = [BackupCode(user=user, code=code) for code in codes]
            BackupCode.objects.bulk_create(backup_codes)
            backup_code_serializer = BackupCodeSerializer(backup_codes, many=True)

            return Response(
                {
                    "status": "success",
                    "detail": "2FA setup completed.",
                    "backup_codes": backup_code_serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            raise exceptions.InvalidTwoFaOrOtp()


class Change2FAMethodView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request):
        user = request.user
        serializer = Change2FAMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_method = serializer.validated_data["new_method"]

        if user.preferred_2fa == new_method:
            return Response(
                {"status": "error", "detail": "This method is already your active 2FA method."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_device = auth_utils.create_2fa_device(user, new_method)
        new_device.save()
        setattr(user, f"{new_method}_device", new_device)
        user.save()

        response_data = {"status": "success"}
        if new_method in ["email", "sms"]:
            new_device.generate_challenge()
            response_data["detail"] = "An email has been sent." if new_method == "email" else "An SMS has been sent."
        else:
            response_data["provisioning_uri"] = new_device.config_url

        return Response(response_data, status=status.HTTP_200_OK)


class CompleteChange2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = CompleteChange2FAMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_method = serializer.validated_data["new_method"]
        code = serializer.validated_data["code"]

        new_device = getattr(user, f"{new_method}_device", None)

        if not new_device or not new_device.verify_token(code):
            raise exceptions.InvalidTwoFaOrOtp()

        new_device.confirmed = True
        new_device.save()

        auth_utils.remove_existing_2fa_devices(user, exclude_method=new_method)

        user.preferred_2fa = new_method
        user.save()

        # Generate new backup codes
        BackupCode.objects.filter(user=user).delete()
        codes = auth_utils.generate_backup_codes()
        backup_codes = [BackupCode(user=user, code=code) for code in codes]
        BackupCode.objects.bulk_create(backup_codes)
        backup_code_serializer = BackupCodeSerializer(backup_codes, many=True)

        return Response(
            {
                "status": "success",
                "detail": "2FA method has been updated successfully.",
                "backup_codes": backup_code_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise exceptions.No2FASetUp()

        if user.preferred_2fa == "totp": # no need to generate challenge
            return Response(
                {"status": "verification_required"},
                status=status.HTTP_202_ACCEPTED,
            )

        device = getattr(user, f"{user.preferred_2fa}_device", None)

        if device:
            device.generate_challenge()
            return Response(
                {"status": "verification_required"},
                status=status.HTTP_202_ACCEPTED,
            )

        raise exceptions.UnknownError()


class CompleteDisable2FAView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    throttle_classes = [TwoFAAnonRateThrottle, TwoFAUserRateThrottle]

    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.preferred_2fa:
            raise exceptions.No2FASetUp()

        serializer = CompleteDisable2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        if not auth_utils.validate_two_fa(user, code):
            raise exceptions.InvalidTwoFaOrOtp()

        method = user.preferred_2fa
        device = getattr(user, f"{method}_device", None)

        if device:
            user.preferred_2fa = None
            device.delete()
            setattr(user, f"{method}_device", None)
            user.save()

        BackupCode.objects.filter(user=user).delete()

        return Response(
            {"status": "success", "detail": "2FA has been disabled."},
            status=status.HTTP_200_OK,
        )


class UsernameChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser]
    serializer_class = UsernameChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        new_username = serializer.validated_data.get("new_username")
        user = request.user

        user.username = new_username
        user.username_change_count += 1
        user.save()

        remaining_changes = (
            settings.MAXIMUM_ALLOWED_USERNAME_CHANGE - user.username_change_count
        )

        response_data = {
            "status": "success",
            "new_username": user.username,
            "remaining_changes": remaining_changes
        }

        return Response(response_data, status=status.HTTP_200_OK)


class EmailChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser, CanChangeEmail]

    def post(self, request, *args, **kwargs):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data.get("new_email")
        user = request.user

        otp = auth_utils.generate_otp(user)
        auth_utils.send_otp_email(otp, recipient_email=new_email)

        cache.set(f"email_change_new_email_{user.id}", new_email, timeout=300)

        return Response(
            {"status": "verification_required"},
            status=status.HTTP_202_ACCEPTED,
        )


class CompleteEmailChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser, CanChangeEmail]

    def post(self, request, *args, **kwargs):
        serializer = CompleteEmailorPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get("code")
        user = request.user

        if not auth_utils.validate_otp(user, code):
            raise exceptions.InvalidTwoFaOrOtp()

        new_email = cache.get(f"email_change_new_email_{user.id}")
        if not new_email:
            raise exceptions.UnknownError()

        user.email = new_email
        user.save()

        cache.delete(f"otp_secret_{user.id}")
        cache.delete(f"email_change_new_email_{user.id}")

        return Response({
            "status": "success",
            "new_email": new_email,
            }, status=status.HTTP_200_OK
        )

class PhoneChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser, CanChangePhone]

    def post(self, request, *args, **kwargs):
        serializer = PhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_phone = serializer.validated_data.get("new_phone")
        user = request.user

        if new_phone == user.phone_number:
            raise CustomAPIException(
                "Your previous phone number can't be same with the new one.",
                status_code=400,
            )
        send_sms_otp_task.delay(str(new_phone), user.id, is_2fa=False)

        cache.set(f"phone_change_new_phone_{user.id}", new_phone, timeout=300)

        return Response(
            {"status": "verification_required"},
            status=status.HTTP_202_ACCEPTED,
        )


class CompletePhoneChangeView(APIView):
    permission_classes = [IsAuthenticated, IsNotOAuthUser, CanChangePhone]

    def post(self, request, *args, **kwargs):
        serializer = CompleteEmailorPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get("code")
        user = request.user

        try:
            otp = cache.get(f"phone_change_otp_{user.id}")
        except Exception:
            raise exceptions.UnknownError()

        if otp != code:
            raise exceptions.InvalidTwoFaOrOtp()

        new_phone = cache.get(f"phone_change_new_phone_{user.id}")
        if not new_phone:
            raise CustomAPIException(
                detail="New Phone not found. try again from the initial step.",
                status_code=401,
            )
        user.phone_number = new_phone
        user.save()

        cache.delete(f"phone_change_otp_{user.id}")
        cache.delete(f"phone_change_new_phone_{user.id}")

        return Response(
            {
                "status": "success",
                "new_phone": str(new_phone)
            }, status=status.HTTP_200_OK
        )


class UserGetView(APIView):
    """
    Retrieve a user based on their exact identifier (email, username, or phone number).
    """
    def get(self, request, *args, **kwargs):
        identifier = request.query_params.get('identifier', '').strip()

        if identifier:
            user = general_utils.get_user_by_identifier(identifier, case_sensitive=False)
            serializer = UserSerializer(user, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise CustomAPIException("Identifier is required.", status_code=status.HTTP_400_BAD_REQUEST)

# make 2fa change verify endpoint better
# TODO: other social auths
# TODO: generate new sets backup codes & complete
# TODO: make all error messages better
# TODO: make otp/2fa expiration time dynamic
# TODO: deactive unverified email after ...
