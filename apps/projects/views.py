
from django.shortcuts import get_object_or_404
from django.db.models import Exists, OuterRef

from rest_framework import status, viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
)

from apps.projects.permissions import IsProjectAllowedByRole
from apps.projects.models import (Project,
    ProjectJoinRequest,
)
from apps.projects.serializers import (
    ProjectJoinRequestSerializer,
    ProjectSerializer,
    ProjectMembershipSerializer,
    AddProjectMemberSerializer,
    ChangeProjectMemberRoleSerializer,
)
from apps.projects.services import (
    approve_project_join_request,
    create_project_join_request,
    create_project,
    add_project_member,
    change_project_member_role,
    remove_project_member,
)
from apps.teams.models import TeamMembership

class ProjectJoinRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    request=None,
    responses={
        201: ProjectJoinRequestSerializer,
    },
)

    def post(self, request, project_id):
        project = get_object_or_404(
            Project,
            id=project_id,
        )

        try:
            join_request = create_project_join_request(
                user=request.user,
                project=project,
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

        serializer = ProjectJoinRequestSerializer(
            join_request
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

class ProjectJoinRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            name="ProjectJoinRequestApproveResponse",
            fields={
                "detail": serializers.CharField(),
                "membership_id": serializers.IntegerField(),
                "user_id": serializers.IntegerField(),
                "project_id": serializers.IntegerField(),
                "role": serializers.CharField(),
            },
        ),
    },
)

    def post(self, request, project_id, request_id):
        project = get_object_or_404(
            Project,
            id=project_id,
        )

        join_request = get_object_or_404(
            ProjectJoinRequest,
            id=request_id,
            project=project,
        )

        try:
            membership = approve_project_join_request(
                join_request_id=join_request.id,
                reviewer=request.user,
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

        return Response(
            {
                "detail": "Join request approved.",
                "membership_id": membership.id,
                "user_id": membership.user_id,
                "project_id": membership.project_id,
                "role": membership.role,
            },
            status=status.HTTP_200_OK,
        )

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.none()


    permission_classes = [
        IsAuthenticated,
        IsProjectAllowedByRole,
    ]

    @action(
        detail=True,
        methods=["get"],
        url_path="members",
    )
    def members(self, request, pk=None):

        project = self.get_object()

        memberships = (
            project.memberships
            .select_related("user")
            .all()
        )

        serializer = ProjectMembershipSerializer(
            memberships,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="members",
    )
    def add_member(self, request, pk=None):

        project = self.get_object()

        serializer = AddProjectMemberSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            membership = add_project_member(
                actor=request.user,
                project=project,
                username=serializer.validated_data["username"],
                role=serializer.validated_data["role"],
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

        response_serializer = ProjectMembershipSerializer(
            membership
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"members/(?P<member_id>[0-9]+)/role",
    )
    def change_member_role(
        self,
        request,
        pk=None,
        member_id=None,
    ):

        project = self.get_object()

        serializer = ChangeProjectMemberRoleSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            membership = change_project_member_role(
                actor=request.user,
                project=project,
                member_id=member_id,
                role=serializer.validated_data["role"],
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

        response_serializer = ProjectMembershipSerializer(
            membership
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"members/(?P<member_id>[0-9]+)",
    )
    def remove_member(
        self,
        request,
        pk=None,
        member_id=None,
    ):

        project = self.get_object()

        try:
            remove_project_member(
                actor=request.user,
                project=project,
                member_id=member_id,
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

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def get_queryset(self):
        user = self.request.user

        team_membership = TeamMembership.objects.filter(
            team=OuterRef("team"),
            user=user,
        )

        return (
            Project.objects
            .annotate(
                user_is_team_member=Exists(team_membership)
            )
            .filter(
                user_is_team_member=True
            )
            .select_related(
                "team",
                "created_by",
            )
        )

    def perform_create(self, serializer):
        team = serializer.validated_data["team"]

        serializer.instance = create_project(
            user=self.request.user,
            team=team,
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
        )
