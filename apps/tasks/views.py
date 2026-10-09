from django.shortcuts import render
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from rest_framework import status, viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tasks.permissions import IsTaskAllowedByProjectRole
from apps.projects.models import ProjectMembership
from apps.tasks.models import Task
from apps.tasks.serializers import TaskClaimSerializer, TaskSerializer
from apps.tasks.services import (
    claim_task,
    unclaim_task,
    complete_task,
)


class TaskClaimView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            201: TaskClaimSerializer,
        },
    )

    def post(self, request, task_id):
        task = get_object_or_404(
            Task,
            id=task_id,
        )

        try:
            claim = claim_task(
                task_id=task.id,
                user=request.user,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TaskClaimSerializer(claim)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

class TaskUnclaimView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: TaskClaimSerializer,
        },
    )

    @extend_schema(
        request=None,
        responses={
            200: TaskClaimSerializer,
        },
    )

    def post(self, request, task_id):
        task = get_object_or_404(
            Task,
            id=task_id,
        )

        try:
            claim = unclaim_task(
                task_id=task.id,
                user=request.user,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TaskClaimSerializer(claim)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class TaskCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: TaskClaimSerializer,
        },
    )

    def post(self, request, task_id):
        task = get_object_or_404(
            Task,
            id=task_id,
        )

        try:
            claim = complete_task(
                task_id=task.id,
                user=request.user,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TaskClaimSerializer(claim)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTaskAllowedByProjectRole, ]
    queryset = Task.objects.none()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "due_date",
        "priority",
        "status",
        "title",
    ]

    ordering = ["-created_at"]

    search_fields = [
    "title",
    "description",
    "tags__name",
    ]


    filterset_fields = [
        "status",
        "priority",
        "project",
    ]

    def get_queryset(self):
        user = self.request.user

        project_membership = ProjectMembership.objects.filter(
            project=OuterRef("project"),
            user=user,
        )

        return (
            Task.objects
            .filter(is_deleted=False)
            .annotate(
                user_is_project_member=Exists(project_membership)
            )
            .filter(user_is_project_member=True)
            .select_related("project", "created_by")
            .prefetch_related("tags")
        )

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]

        is_project_member = ProjectMembership.objects.filter(
            project=project,
            user=self.request.user,
        ).exists()

        if not is_project_member:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You must be a project member to create a task."
            )

        serializer.save(
            created_by=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone

        task = self.get_object()

        task.is_deleted = True
        task.deleted_at = timezone.now()
        task.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
