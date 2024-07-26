from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from engine.models import Chat
from bookmark.models import Bookmark
from project.models import Project
from engine.serializers import ChatSerializer
from bookmark.serializers import BookmarkSerializer
from project.serializers import ProjectSerializer
from share.models import AccessRequest


class GenerateShareableLinkView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You do not have permission to generate a link for this item.")

        if not obj.shareable_key:
            obj.shareable_key = obj.generate_shareable_key()


        return Response({'shareable_key': obj.shareable_key}, status=200)

    def get_object(self):
        raise NotImplementedError("Subclasses should implement this method.")


class AccessSharedContentView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        shareable_key = kwargs.get('shareable_key')
        if not shareable_key:
            return Response({
                "status": "error",
                "detail": "Shareable key is required."
            }, status=400)


        obj = None
        for model in [Chat, Bookmark, Project]:
            obj = model.objects.filter(shareable_key=shareable_key).first()
            if obj:
                break

        if obj is None:
            raise NotFound("Content not found.")

        # Check if the user has access
        if request.user in obj.viewers.all() or obj.user == request.user:
            serializer = self.get_serializer(obj)
            return Response(serializer.data)

        # If the user is not in the viewers, create an access request
        success = self.create_access_request(request.user, obj)

        if success:
            return Response({
                "status": "success",
                "detail": "Access request sent to the owner."
            }, status=202)
        else:
            return Response({
                "status": "error",
                "detail": "You have already requested access to this content."
            },
                            status=status.HTTP_400_BAD_REQUEST)


    def notify_owner(self, owner, access_request):
        print("hi")
        subject = "New Access Request"
        approval_link = f"{settings.FRONTEND_URL}/approve-access/{access_request.approval_uuid}/"
        message = f"A user has requested access to your content. Approve the request using the following link: {approval_link}"
        owner.send_mail(subject, message)

    def create_access_request(self, user, obj):
        content_type = ContentType.objects.get_for_model(obj)

        # Check if an access request from the user for this content already exists
        if AccessRequest.objects.filter(
                user=user,
                content_type=content_type,
                object_id=obj.id
        ).exists():
            return False


        access_request = AccessRequest.objects.create(
            user=user,
            content_type=content_type,
            object_id=obj.id
        )

        # Notify the owner
        self.notify_owner(obj.user, access_request)
        return True

    def get_serializer(self, obj):
        if isinstance(obj, Chat):
            return ChatSerializer(obj)
        elif isinstance(obj, Bookmark):
            return BookmarkSerializer(obj)
        elif isinstance(obj, Project):
            return ProjectSerializer(obj)
        return None


class ApproveAccessRequestView(APIView):
    def get(self, request, approval_uuid):
        access_request = get_object_or_404(AccessRequest, approval_uuid=approval_uuid)

        if access_request.is_approved:
            return Response({
                "status":"error",
                "detail": "This request has already been approved."
            }, status=status.HTTP_400_BAD_REQUEST)


        if request.user != access_request.content_object.user:
            return Response({
                "status": "error",
                "detail": "You do not have permission to approve this request."
            },
            status=status.HTTP_403_FORBIDDEN)

        # Add the user to the viewers list
        access_request.content_object.viewers.add(access_request.user)
        access_request.approved = True
        access_request.save()

        return Response({
            "status": "success",
            "detail": "Access request approved."
        }, status=status.HTTP_200_OK)