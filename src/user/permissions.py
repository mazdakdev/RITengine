from rest_framework import status
from rest_framework.permissions import BasePermission
from RITengine.exceptions import CustomAPIException
class IsNotOAuthUser(BasePermission):
    message = "Access restricted for OAuth-based users."

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_oauth_based:
            raise CustomAPIException(self.message, status_code=status.HTTP_403_FORBIDDEN)
        return True

class CanChangeEmail(BasePermission):
    message = "You cannot change your E-mail while E-mail based 2FA is active."

    def has_permission(self, request, view):
        user = request.user
        if user.preferred_2fa == 'email':
            raise CustomAPIException(self.message, status_code=status.HTTP_403_FORBIDDEN)
        return True

class CanChangePhone(BasePermission):
    message = "You cannot change your Phone Number while E-mail based 2FA is active."

    def has_permission(self, request, view):
        user = request.user
        if user.preferred_2fa == 'phone':
           raise CustomAPIException(self.message, status_code=status.HTTP_403_FORBIDDEN)
        return True
