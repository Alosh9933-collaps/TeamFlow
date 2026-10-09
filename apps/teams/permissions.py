from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.teams.models import TeamMembership


class IsTeamAllowedByRole(BasePermission):
    message = "You do not have permission to perform this action."

    def get_role(self, user, team):
        return (
            TeamMembership.objects
            .filter(
                user=user,
                team=team,
            )
            .values_list(
                "role",
                flat=True,
            )
            .first()
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        role = self.get_role(
            request.user,
            obj,
        )

        if role is None:
            return False

        if request.method in SAFE_METHODS:
            return True

        if view.action in [
            "add_member",
        ]:
            return role in {
                TeamMembership.Role.OWNER,
                TeamMembership.Role.ADMIN,
            }

        if view.action in [
            "update",
            "partial_update",
            "destroy",
            "change_member_role",
            "remove_member",

        ]:
            return role == TeamMembership.Role.OWNER

        return False
