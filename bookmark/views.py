from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from bookmark.serializers import BookmarkSerializer
from .models import Bookmark


class BookmarksListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarksDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = BookmarkSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)
