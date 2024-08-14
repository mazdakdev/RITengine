from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from share.views import GenerateShareableLinkView
from .models import Project, Message
from .serializers import ProjectSerializer, MessageIDSerializer, MessageProjectAssociationSerializer
from engine.serializers import MessageSerializer
from django_filters import rest_framework as filters
from .filters import ProjectFilter
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

class ProjectMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        messages = project.messages.all()
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        serializer = MessageIDSerializer(data=request.data)

        if serializer.is_valid():
            message_ids = serializer.validated_data['message_ids']
            messages = Message.objects.filter(id__in=message_ids)
            for message in messages:
                project.messages.add(message)
                project.save()
            return Response(MessageSerializer(messages, many=True, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        serializer = MessageIDSerializer(data=request.data)

        if serializer.is_valid():
            message_ids = serializer.validated_data['message_ids']
            messages = project.messages.filter(id__in=message_ids)
            project.messages.remove(*messages)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GenerateProjectLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Project, id=self.kwargs.get('id'))

class MessageProjectAssociationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = MessageProjectAssociationSerializer(data=request.data)
        if serializer.is_valid():
            message_id = serializer.validated_data['message_id']
            project_ids = serializer.validated_data['project_ids']

        
            message = Message.objects.get(id=message_id)


            projects = Project.objects.filter(id__in=project_ids)
            message.projects.add(*projects)

            return Response({'status': 'projects added to message'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ManageProjectsInMessageView(APIView):
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
        
        for project_id in project_ids:
            project = get_object_or_404(Project, id=project_id, user=user)
            message.projects.remove(project)

        message.save()
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
class ManageMessagesInProjectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, id):
        user = request.user
        project = get_object_or_404(Project, id=id, user=user)
        message_ids = request.data.get('message_ids', [])
        
        for message_id in message_ids:
            message = get_object_or_404(Message, id=message_id, chat__user=user)
            project.messages.add(message)

        project.save()
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        project = get_object_or_404(Project, id=id, user=user)
        message_ids = request.data.get('message_ids', [])
        
        for message_id in message_ids:
            message = get_object_or_404(Message, id=message_id, chat__user=user)
            project.messages.remove(message)

        project.save()
        serializer = ProjectSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
