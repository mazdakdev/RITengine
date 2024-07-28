from RITengine.exceptions import CustomAPIException
from rest_framework import status

class InvalidCredentials(CustomAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid Credentials."
    default_code = "invalid_credentials"

class TwoFactorRequired(CustomAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '2FA Token is required.'
    default_code = '2fa_required'

class EmailNotVerified(CustomAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "User's E-mail is not yet verified."
    default_code = 'email_not_verified'