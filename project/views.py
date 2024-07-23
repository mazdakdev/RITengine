from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Project, Message
from .serializers import ProjectSerializer
from engine.serializers import MessageSerializer

class UserProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

class ProjectMessagesListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated,]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        projects = Project.objects.filter(user=self.request.user, id=project_id)

        return Message.objects.filter(projects__in=projects)
class ProjectCreateView(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated,]
    lookup_field = 'id'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)


class AddMessageToProjectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request, project_id, message_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            raise NotFound('Project not found or you do not have permission to access it.')

        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            raise NotFound('Message not found.')

        project.messages.add(message)
        return Response({'status': 'message added to project'}, status=status.HTTP_200_OK)

#TODO: Better Error Handling