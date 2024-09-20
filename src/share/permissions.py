from rest_framework import permissions
from rest_framework.permissions import BasePermission
from engine.models import Message

class IsOwnerOrViewer(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if isinstance(obj, Message):
                return request.user == obj.chat.user or request.user in obj.chat.viewers.all()
            return request.user == obj.user or request.user in obj.viewers.all()

        if request.user == obj.user:
            return True
        return False
