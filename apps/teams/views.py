from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.teams.models import Team
from apps.teams.permissions import IsTeamAllowedByRole
from apps.teams.serializers import (
    TeamSerializer,
    TeamMembershipSerializer,
    AddTeamMemberSerializer,
    ChangeTeamMemberRoleSerializer,
)
from apps.teams.services import (
    create_team,
    get_user_teams,
    add_team_member,
    change_team_member_role,
    remove_team_member,
)


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    queryset = Team.objects.none()

    permission_classes = [
        IsAuthenticated,
        IsTeamAllowedByRole,
    ]

    @action(
        detail=True,
        methods=["get"],
        url_path="members",
        )
    def members(self, request, pk=None):

        team = self.get_object()

        memberships = (
            team.memberships
            .select_related("user")
            .all()
        )

        serializer = TeamMembershipSerializer(
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

        team = self.get_object()

        serializer = AddTeamMemberSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            membership = add_team_member(
                actor=request.user,
                team=team,
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

        response_serializer = TeamMembershipSerializer(
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

        team = self.get_object()

        serializer = ChangeTeamMemberRoleSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            membership = change_team_member_role(
                actor=request.user,
                team=team,
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

        response_serializer = TeamMembershipSerializer(
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

        team = self.get_object()

        try:
            remove_team_member(
                actor=request.user,
                team=team,
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
        return get_user_teams(
            self.request.user
        )

    def perform_create(self, serializer):
        team = create_team(
            user=self.request.user,
            name=serializer.validated_data["name"],
        )

        serializer.instance = team
