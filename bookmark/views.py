from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from bookmark.serializers import BookmarkSerializer
from share.views import GenerateShareableLinkView
from rest_framework.response import Response
from .models import Bookmark
from .filters import BookmarkFilter
from collections import defaultdict

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

class GenerateBookmarkLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Bookmark, id=self.kwargs.get('id'))