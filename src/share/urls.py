from django.urls import path
from .views import (
        AccessSharedContentView, ApproveAccessRequestView,
        SharedWithMeView, SharedByMeView
    )

urlpatterns = [
    path('shared-with-me/', SharedWithMeView.as_view(), name='shared_with_me'),
    path('shared-by-me/', SharedByMeView.as_view(), name='shared_by_me'),
    path('<str:shareable_key>/', AccessSharedContentView.as_view(), name='access_shared_content'),
    path('approve-access/<uuid:approval_uuid>/', ApproveAccessRequestView.as_view(), name='approve_access_request'),
]
