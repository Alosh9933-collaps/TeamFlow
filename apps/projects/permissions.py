from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.projects.models import ProjectMembership
from apps.teams.models import TeamMembership


class IsProjectAllowedByRole(BasePermission):
    message = "You do not have permission to perform this action."

    def _get_team_role(self, user, team):
        return (
            TeamMembership.objects
            .filter(
                user=user,
                team=team,
            )
            .values_list("role", flat=True)
            .first()
        )

    def _get_project_role(self, user, project):
        return (
            ProjectMembership.objects
            .filter(
                user=user,
                project=project,
            )
            .values_list("role", flat=True)
            .first()
        )

    def has_permission(self, request, view):
        if request.method == "POST":
            team_id = request.data.get("team")

            if not team_id:
                return True

            role = (
                TeamMembership.objects
                .filter(
                    user=request.user,
                    team_id=team_id,
                )
                .values_list("role", flat=True)
                .first()
            )

            return role in {
                TeamMembership.Role.OWNER,
                TeamMembership.Role.ADMIN,
            }

        return True

    def has_object_permission(self, request, view, obj):
        team_role = self._get_team_role(
            request.user,
            obj.team,
        )

        if team_role is None:
            return False

        if request.method in SAFE_METHODS:
            return True

        project_role = self._get_project_role(
            request.user,
            obj,
        )

        if team_role in {
            TeamMembership.Role.OWNER,
            TeamMembership.Role.ADMIN,
        }:
            return True

        return project_role == ProjectMembership.Role.MANAGER
