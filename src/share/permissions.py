from rest_framework.permissions import BasePermission

class IsOwnerOrViewer(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user == obj.user or request.user in obj.viewers.all()

        if request.user == obj.user:
            return True

        return False
