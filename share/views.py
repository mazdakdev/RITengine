from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from engine.models import Chat
from bookmark.models import Bookmark
from project.models import Project
from engine.serializers import ChatSerializer
from bookmark.serializers import BookmarkSerializer
from project.serializers import ProjectSerializer

class GenerateShareableLinkView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You do not have permission to generate a link for this item.")

        if not obj.shareable_key:
            obj.shareable_key = obj.generate_shareable_key()
            obj.save()


        return Response({'shareable_key': obj.shareable_key}, status=200)

    def get_object(self):
        raise NotImplementedError("Subclasses should implement this method.")


class AccessSharedContentView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        shareable_key = kwargs.get('shareable_key')
        if not shareable_key:
            return Response({"detail": "Shareable key is required."}, status=400)

        # Try to find the object by its shareable_key
        obj = None
        for model in [Chat, Bookmark, Project]:
            obj = model.objects.filter(shareable_key=shareable_key).first()
            if obj:
                break

        if obj is None:
            raise NotFound("Content not found.")

        # Check permissions
        if request.user not in obj.viewers.all() and obj.user != request.user:
            raise PermissionDenied("You do not have access to view this item.")

        # Return serialized data
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def get_serializer(self, obj):
        if isinstance(obj, Chat):
            return ChatSerializer(obj)
        elif isinstance(obj, Bookmark):
            return BookmarkSerializer(obj)
        elif isinstance(obj, Project):
            return ProjectSerializer(obj)
        return None