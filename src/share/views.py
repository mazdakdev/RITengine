from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from RITengine.exceptions import CustomAPIException
from engine.models import Chat
from bookmark.models import Bookmark
from project.models import Project
from engine.serializers import ChatSerializer
from bookmark.serializers import BookmarkSerializer
from project.serializers import ProjectSerializer
from share.models import AccessRequest
from .serializers import GenerateShareableLinkSerializer
from user.serializers import UserSerializer

User = get_user_model()

class GenerateShareableLinkView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = GenerateShareableLinkSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("You do not have the permission to generate a link for this item.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not obj.shareable_key:
            obj.shareable_key = obj.generate_shareable_key()
            obj.save()

        user_ids = serializer.validated_data.get('user_ids', [])
        if user_ids:
            self.add_viewers(user_ids, obj)

        return Response({
            'status': 'success',
            'shareable_key': obj.shareable_key
        }, status=200)

    def add_viewers(self, user_ids, obj):
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            if user not in obj.viewers.all():
                obj.viewers.add(user)
                self.notify_user(user, obj)

    def notify_user(self, user, obj):
        subject = "You have been granted access to shared content"
        message = f"You have been granted access to {obj}."
        user.send_text_email(subject, message)
        print(subject, message) #TODO:

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
            serializer = self.get_serializer(obj, request)
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
        owner.send_text_email(subject, message)

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

    def get_serializer(self, obj, request):
        if isinstance(obj, Chat):
            return ChatSerializer(obj)
        elif isinstance(obj, Bookmark):
            return BookmarkSerializer(obj)
        elif isinstance(obj, Project):
            return ProjectSerializer(obj, context={"user":request.user})
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


class BaseViewersListView(generics.GenericAPIView):
    """
    Base class to list, add, or remove viewers for any model that has viewers.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        obj = self.get_object()
        return obj.viewers.all()

    def get_object(self):
        """
        Subclasses must implement this method to return the object
        (e.g., Project, Bookmark, Chat) for which viewers are being managed.
        """
        raise NotImplementedError("Subclasses must implement the get_object method.")

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        viewers = self.get_queryset()
        serializer = self.get_serializer(viewers, many=True)
        response_data = {
                "viewers": serializer.data,
                "sharable_key": obj.shareable_key
            }
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.user != request.user:
            raise CustomAPIException("Item not found", status_code=status.HTTP_404_NOT_FOUND)

        user_ids = request.data.get('user_ids', [])
        if not isinstance(user_ids, list):
            raise CustomAPIException("user_ids must be a list.")

        users = User.objects.filter(id__in=user_ids)

        existing_viewers = obj.viewers.filter(id__in=user_ids).values_list('id', flat=True)
        if existing_viewers:
            raise CustomAPIException(f"Some users are already viewers: {list(existing_viewers)}")

        obj.viewers.add(*users)

        for user in users:
            self.notify_user(user, obj)

        updated_viewers = obj.viewers.all()
        serializer = self.get_serializer(updated_viewers, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.user != request.user:
            raise CustomAPIException("Item not found", status_code=status.HTTP_404_NOT_FOUND)

        user_ids = request.data.get('user_ids', [])
        if not isinstance(user_ids, list):
            raise CustomAPIException("user_ids must be a list.")

        users = User.objects.filter(id__in=user_ids)

        non_existing_viewers = set(user_ids) - set(obj.viewers.values_list('id', flat=True))
        if non_existing_viewers:
            raise CustomAPIException(f"Some users are not viewers: {list(non_existing_viewers)}")

        obj.viewers.remove(*users)

        for user in users:
            self.notify_user(user, obj)

        updated_viewers = obj.viewers.all()
        serializer = self.get_serializer(updated_viewers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def notify_user(self, user, obj):
        subject = "You've been added as a viewer"
        message = f"You've been added as a viewer to the {obj.__class__.__name__.lower()} of {user.first_name}."
        # Send an email or notification here
        user.send_text_email(subject, message)


class SharedWithMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        query_params = request.query_params

        data = {}

        if 'projects' in query_params:
            shared_projects = Project.objects.filter(viewers=user)
            project_serializer = ProjectSerializer(shared_projects, many=True, context={'request': request})
            data['projects'] = project_serializer.data

        if 'bookmark' in query_params:
            shared_bookmarks = Bookmark.objects.filter(viewers=user)
            bookmark_serializer = BookmarkSerializer(shared_bookmarks, many=True, context={'request': request})
            data['bookmark'] = bookmark_serializer.data

        if 'chats' in query_params:
            shared_chats = Chat.objects.filter(viewers=user)
            chat_serializer = ChatSerializer(shared_chats, many=True, context={'request': request})
            data['chats'] = chat_serializer.data

        if not data:
            return Response({'status': 'error', 'message': 'No valid query parameters provided.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': "success",
            **data,
        }, status=status.HTTP_200_OK)


class SharedByMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        query_params = request.query_params

        data = {}

        if 'projects' in query_params:
            shared_projects = Project.objects.filter(user=user, viewers__isnull=False).distinct()
            project_serializer = ProjectSerializer(shared_projects, many=True, context={'request': request})
            data['projects'] = project_serializer.data

        if 'bookmark' in query_params:
            shared_bookmarks = Bookmark.objects.filter(user=user, viewers__isnull=False).distinct()
            bookmark_serializer = BookmarkSerializer(shared_bookmarks, many=True, context={'request': request})
            data['bookmark'] = bookmark_serializer.data

        if 'chats' in query_params:
            shared_chats = Chat.objects.filter(user=user, viewers__isnull=False).distinct()
            chat_serializer = ChatSerializer(shared_chats, many=True, context={'request': request})
            data['chats'] = chat_serializer.data

        if not data:
            return Response({'status': 'error', 'message': 'No valid query parameters provided.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            **data,
        }, status=status.HTTP_200_OK)
