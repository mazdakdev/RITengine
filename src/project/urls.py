from django.urls import path
from .views import (
    ProjectListCreateView, ProjectRetrieveUpdateDestroyView,
    GenerateProjectLinkView, MessagesInProjectView,
    ProjectViewersListView
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project_list'),
    path('<str:id>/', ProjectRetrieveUpdateDestroyView.as_view(), name='project_detail'),
    path('<int:id>/messages/',  MessagesInProjectView.as_view(), name='messages_in_project'),
    path('<int:id>/viewers/',  ProjectViewersListView.as_view(), name='project_viewers'),
    path('<int:id>/generate-link/', GenerateProjectLinkView.as_view(), name='project_link'),
]
