from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectRetrieveUpdateDestroyView,
    ProjectMessages,
    GenerateProjectLinkView,
    MessageProjectAssociationView

)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list'),
    path('<int:id>/', ProjectRetrieveUpdateDestroyView.as_view(), name='project_detail'),
    path('<int:project_id>/messages/', ProjectMessages.as_view(), name='project_messages_list'),
    path('messages-projects/',  MessageProjectAssociationView.as_view(), name='message-project-association'),
    path('<int:id>/generate-link/', GenerateProjectLinkView.as_view(), name='project_link'),
]
