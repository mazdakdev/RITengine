from django.urls import path
from .views import (
    UserProjectListView,
    ProjectMessagesListView,
    ProjectCreateView,
    ProjectRetrieveUpdateDestroyView,
    AddMessageToProjectView,
    GenerateProjectLinkView
)

urlpatterns = [
    path('', UserProjectListView.as_view(), name='user_project_list'),
    path('<int:project_id>/messages/', ProjectMessagesListView.as_view(), name='project_messages_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('<int:id>/', ProjectRetrieveUpdateDestroyView.as_view(), name='project_detail'),
    path('<int:project_id>/add-message/<int:message_id>/', AddMessageToProjectView.as_view(), name='add_msg_to_proj'),
    path('<int:id>/generate-link/', GenerateProjectLinkView.as_view(), name='project_link'),
]

