from django.urls import path
from .views import (
    UserProjectListCreateView,
    ProjectMessagesListView,
    ProjectRetrieveUpdateDestroyView,
    GenerateProjectLinkView
)

urlpatterns = [
    path('', UserProjectListCreateView.as_view(), name='user_project_list'),
    path('<int:project_id>/messages/', ProjectMessagesListView.as_view(), name='project_messages_list'),
    path('<int:id>/', ProjectRetrieveUpdateDestroyView.as_view(), name='project_detail'),
    path('<int:id>/generate-link/', GenerateProjectLinkView.as_view(), name='project_link'),
]
#delete no content error