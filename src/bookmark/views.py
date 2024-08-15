from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from bookmark.serializers import BookmarkSerializer
from share.views import GenerateShareableLinkView
from rest_framework.response import Response
from rest_framework import status
from .models import Bookmark
from engine.models import Message
from .filters import BookmarkFilter
from engine.serializers import MessageSerializer
from collections import defaultdict
from RITengine.exceptions import CustomAPIException
from rest_framework.views import APIView

class BookmarksListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer
    filterset_class = BookmarkFilter

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        grouped_data = self.group_by_date(serializer.data)
        return Response(grouped_data)

    def group_by_date(self, data):
        grouped_bookmarks = defaultdict(list)
        for item in data:
            date_key = item['created_at'].split("T")[0]
            grouped_bookmarks[date_key].append(item)
        return grouped_bookmarks

class BookmarksDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = BookmarkSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

class BookmarkMessageView(APIView):
    """
    Toggles the bookmark status of the specified message using a one-to-one relationship
    with the Bookmark model. 

    Returns the message object with the updated 'is_bookmarked' status (True/False).
    """
    permission_classes = [IsAuthenticated, ]

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user )
        
        if Bookmark.objects.filter(message=message).exists():
            raise CustomAPIException(
                detail='Message is already bookmarked',
                status_code=400
            )

        bookmark = Bookmark.objects.create(message=message, user=user)
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        bookmark = get_object_or_404(Bookmark, message=message, user=user)
        bookmark.delete()
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class GenerateBookmarkLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Bookmark, id=self.kwargs.get('id'))