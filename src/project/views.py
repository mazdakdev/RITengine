from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from share.views import GenerateShareableLinkView, BaseViewersListView, SharedRetrieveUpdateDestroyView
from .models import Project, Message
from .serializers import ProjectSerializer
from engine.serializers import MessageSerializer
from .filters import ProjectFilter
from rest_framework.pagination import PageNumberPagination
from share.permissions import IsOwnerOrViewer
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ProjectFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        customer = getattr(self.request.user, 'customer', None)

        if customer:
            project = serializer.save(user=self.request.user)
            customer.can_create_project()
            customer.projects_created += 1
            customer.save()

            if 'viewers' in serializer.validated_data:
                project.viewers.add(*serializer.validated_data['viewers'])

            return project
        else:
            raise PermissionDenied("You must have an active subscription to create projects.")

class ProjectRetrieveUpdateDestroyView(SharedRetrieveUpdateDestroyView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class GenerateProjectLinkView(GenerateShareableLinkView):
    def get_object(self):
        return get_object_or_404(Project, id=self.kwargs.get('id'))

class ProjectsInMessageView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        projects = message.projects.all()
        serializer = ProjectSerializer(projects, many=True, context={'user': user})
        return Response(serializer.data)

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        project_ids = request.data.get('project_ids', [])

        for project_id in project_ids:
            project = get_object_or_404(Project, id=project_id, user=user)
            message.projects.add(project)

        message.save()
        serializer = MessageSerializer(message, context={'user': user})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id, chat__user=user)
        project_ids = request.data.get('project_ids', [])
        serializer = MessageSerializer(message, context={'user': user})

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
    permission_classes = [IsAuthenticated, IsOwnerOrViewer]
    pagination_class = PageNumberPagination

    def get(self, request, id):
        project = get_object_or_404(Project, id=id)
        self.check_object_permissions(request, project)
        messages = project.messages.all()
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, id):
        project = get_object_or_404(Project, id=id)
        self.check_object_permissions(request, project)
        message_ids = request.data.get('message_ids', [])

        for message_id in message_ids:
            message = get_object_or_404(Message, id=message_id)
            self.check_object_permissions(request, message)
            project.messages.add(message)

        project.save()
        serializer = ProjectSerializer(project, context={'request':request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        project = get_object_or_404(Project, id=id)
        self.check_object_permissions(request, project)
        serializer = ProjectSerializer(project, context={'request': request})
        message_ids = request.data.get('message_ids', [])

        if message_ids == []:
            project.messages.clear()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif message_ids is not None:
            for message_id in message_ids:
                message = get_object_or_404(Message, id=message_id)
                self.check_object_permissions(request, message)
                project.messages.remove(message)

        project.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProjectViewersListView(BaseViewersListView):
    def get_object(self):
        project_id = self.kwargs.get('id')
        return get_object_or_404(Project, id=project_id)
