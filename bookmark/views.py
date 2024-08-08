from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from bookmark.serializers import BookmarkSerializer
from share.views import GenerateShareableLinkView
from rest_framework.response import Response
from .models import Bookmark


class BookmarksListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class BookmarksDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = BookmarkSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)

class GenerateBookmarkLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Bookmark, id=self.kwargs.get('id'))