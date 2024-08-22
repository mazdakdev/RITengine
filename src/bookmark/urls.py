from django.urls import path
from bookmark.views import (
    BookmarksListView, BookmarksDetailView,
    GenerateBookmarkLinkView, BookmarkViewersListView
)

urlpatterns = [
    path('', BookmarksListView.as_view(), name='bookmark_list'),
    path('<int:id>/', BookmarksDetailView.as_view(), name='bookmark_detail'),
    path('<int:id>/viewers/', BookmarkViewersListView.as_view(), name='bookmark_viewers'),
    path('<int:id>/generate-link/', GenerateBookmarkLinkView.as_view(), name='bookmark_link'),
]
