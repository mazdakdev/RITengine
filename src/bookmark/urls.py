from django.urls import path
from bookmark.views import (
    BookmarksListView,
    BookmarksDetailView,
    GenerateBookmarkLinkView
)

urlpatterns = [
    path('', BookmarksListView.as_view(), name='bookmark_list'),
    path('<int:id>/', BookmarksDetailView.as_view(), name='bookmark_detail'),
    path('<int:id>/generate-link/', GenerateBookmarkLinkView.as_view(), name='bookmark_link'),
]