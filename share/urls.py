from django.urls import path
from .views import AccessSharedContentView

urlpatterns = [
    path('<str:shareable_key>/', AccessSharedContentView.as_view(), name='access_shared_content'),
]