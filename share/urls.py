from django.urls import path
from .views import AccessSharedContentView, ApproveAccessRequestView

urlpatterns = [
    path('<str:shareable_key>/', AccessSharedContentView.as_view(), name='access_shared_content'),
    path('approve-access/<uuid:approval_uuid>/', ApproveAccessRequestView.as_view(), name='approve_access_request'),
]