from django.urls import path
from bookmark.views import (
    BookmarksDetailView,
    GenerateBookmarkLinkView, BookmarkViewersListView
)

urlpatterns = [
    path('', BookmarksDetailView.as_view(), name='bookmark_list'),
    path('<str:id>', BookmarksDetailView.as_view(), name='bookmark_list'),
    path('viewers/', BookmarkViewersListView.as_view(), name='bookmark_viewers'),
    path('generate-link/', GenerateBookmarkLinkView.as_view(), name='bookmark_link'),
]
