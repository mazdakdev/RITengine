from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
class IsNotOAuthUser(BasePermission):
    message = "Access restricted for OAuth-based users."

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_oauth_based:
            raise PermissionDenied(self.message)
        return True