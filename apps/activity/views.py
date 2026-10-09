from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from apps.activity.serializers import ActivityLogSerializer
from apps.activity.services import get_project_activity

from apps.projects.models import Project
from apps.projects.permissions import IsProjectAllowedByRole


class ProjectActivityListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsProjectAllowedByRole,
    ]

    @extend_schema(
        responses=ActivityLogSerializer(many=True),
    )

    def get(self, request, project_id):

        project = get_object_or_404(
            Project,
            id=project_id,
        )

        self.check_object_permissions(
            request,
            project,
        )

        activities = get_project_activity(
            project=project,
        )

        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(
            activities,
            request,
            view=self,
        )

        serializer = ActivityLogSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )
