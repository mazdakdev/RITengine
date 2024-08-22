from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from share.views import GenerateShareableLinkView, BaseViewersListView
from user.serializers import UserSerializer
from .models import Project, Message
from .serializers import ProjectSerializer, MessageProjectAssociationSerializer
from engine.serializers import MessageSerializer
from django_filters import rest_framework as filters
from user.exceptions import CustomAPIException
from .filters import ProjectFilter


User = get_user_model()

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ProjectFilter

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated,]
    lookup_field = 'id'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user, id=self.kwargs['id'])

class GenerateProjectLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Project, id=self.kwargs.get('id'))

class ProjectsInMessageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        project_ids = request.data.get('project_ids', [])

        for project_id in project_ids:
            project = get_object_or_404(Project, id=project_id, user=user)
            message.projects.add(project)

        message.save()
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        project_ids = request.data.get('project_ids', [])
        serializer = MessageSerializer(message, context={'request': request})

        if project_ids == []:
            message.projects.clear()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif project_ids is not None:
            for project_id in project_ids:
                project = get_object_or_404(Project, id=project_id, user=user)
                message.projects.remove(project)

            message.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

class MessagesInProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        project = get_object_or_404(Project, id=id, user=request.user)
        messages = project.messages.all()
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, id):
        user = request.user
        project = get_object_or_404(Project, id=id, user=user)
        message_ids = request.data.get('message_ids', [])

        for message_id in message_ids:
            message = get_object_or_404(Message, id=message_id, chat__user=user)
            project.messages.add(message)

        project.save()
        serializer = ProjectSerializer(project, context={'request':request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        project = get_object_or_404(Project, id=id, user=user)
        serializer = ProjectSerializer(project, context={'request': request})
        message_ids = request.data.get('message_ids', [])

        if message_ids == []:
            project.messages.clear()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif message_ids is not None:
            for message_id in message_ids:
                message = get_object_or_404(Message, id=message_id, chat__user=user)
                project.messages.remove(message)

        project.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectViewersListView(BaseViewersListView):
    def get_object(self):
        project_id = self.kwargs.get('id')
        return get_object_or_404(Project, id=project_id)
