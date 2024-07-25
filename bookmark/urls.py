from django.urls import path
from bookmark.views import (
    BookmarksListView,
    BookmarksDetailView
)

urlpatterns = [
    path('bookmarks/', BookmarksListView.as_view(), name='bookmarks_list'),
    path('bookmarks/<int:id>/', BookmarksDetailView.as_view(), name='bookmarks_detail'),
]