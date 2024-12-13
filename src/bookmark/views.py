from rest_framework import generics, request
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from bookmark.serializers import BookmarkSerializer
from share.views import GenerateShareableLinkView, BaseViewersListView
from rest_framework.response import Response
from rest_framework import status
from .models import Bookmark
from engine.models import Message
from engine.serializers import MessageSerializer
from RITengine.exceptions import CustomAPIException
from rest_framework.views import APIView
from share.permissions import IsOwnerOrViewer
from rest_framework.exceptions import PermissionDenied

class BookmarksDetailView(generics.RetrieveUpdateAPIView):
    """
    Singleton like logic applied for now.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrViewer]
    serializer_class = BookmarkSerializer

    def get_object(self):
            bookmark_id = self.kwargs.get('id')
            customer = getattr(self.request.user, 'customer', None)

<<<<<<< HEAD
            if bookmark_id is not None:
                try:
                    bookmark = Bookmark.objects.get(
                        Q(id=bookmark_id) & (Q(user=self.request.user) | Q(viewers=self.request.user))
                    )
                except Bookmark.DoesNotExist:
                    raise CustomAPIException("Bookmark not found", status_code=404)
            else:
                if customer:
                    # Check if the customer can create more bookmarks
                    if customer.bookmarks_created >= customer.subscription.plan.bookmarks_limit:
                        raise PermissionDenied("You have reached the maximum number of bookmarks allowed by your subscription plan.")
                    bookmark, created = Bookmark.objects.get_or_create(user=self.request.user)
                    if created:
                        customer.bookmarks_created += 1
                        customer.save()
                else:
                    raise PermissionDenied("You must have an active subscription to create bookmarks.")
=======
        if bookmark_id is not None:
            try:
                bookmark = Bookmark.objects.get(id=bookmark_id)
                self.check_object_permissions(self.request, bookmark)
            except Bookmark.DoesNotExist:
                raise NotFound("Bookmark not found.")
        else:
            bookmark, created = Bookmark.objects.get_or_create(user=self.request.user)
>>>>>>> main

            return bookmark

class BookmarkMessageView(APIView):
    """
    Toggles the bookmark status of the specified message within the user's bookmark collection.

    POST: Adds the message to the user's bookmark collection.
    DELETE: Removes the message from the user's bookmark collection.

    Returns the message object with the updated 'is_bookmarked' status (True/False).
    """
    permission_classes = [IsAuthenticated]

    def get_or_create_bookmark(self, user):
        """
        Gets the user's bookmark instance. Creates one if it does not exist.
        """
        bookmark, created = Bookmark.objects.get_or_create(user=user)
        return bookmark

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)

        customer = getattr(user, 'customer', None)
        if not customer or not customer.has_active_subscription():
            raise PermissionDenied("You must have an active subscription to create more bookmarks.")

        if customer.bookmarks_created >= customer.subscription.plan.bookmarks_limit:
            raise PermissionDenied("You have reached the maximum number of bookmarks allowed by your subscription plan.")

        bookmark = self.get_or_create_bookmark(user)

        customer.bookmarks_created += 1
        customer.save()

        bookmark, created = Bookmark.objects.get_or_create(user=user)
        if created:
            customer.bookmarks_created += 1
            customer.save()

        if bookmark.messages.filter(id=message_id).exists():
                        raise CustomAPIException(
                            detail='Message is already bookmarked',
                            status_code=400
                        )

        bookmark.messages.add(message)

        serializer = MessageSerializer(message, context={'user': user})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def delete(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)

        bookmark = self.get_or_create_bookmark(user)

        if not bookmark.messages.filter(id=message_id).exists():
            raise CustomAPIException(
                detail='Message is not bookmarked',
                status_code=400
            )

        bookmark.messages.remove(message)

        serializer = MessageSerializer(message, context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)

class GenerateBookmarkLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Bookmark, user=self.request.user)

class BookmarkViewersListView(BaseViewersListView):
    def get_object(self):
        return get_object_or_404(Bookmark, user=self.request.user)
