from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.projects.models import ProjectMembership


class IsTaskAllowedByProjectRole(BasePermission):
    message = "You do not have permission to perform this action."

    def _get_role(self, user, project):
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
            project_id = request.data.get("project")

            if not project_id:
                return True

            role = (
                ProjectMembership.objects
                .filter(
                    user=request.user,
                    project_id=project_id,
                )
                .values_list("role", flat=True)
                .first()
            )

            return role in {
                ProjectMembership.Role.MANAGER,
                ProjectMembership.Role.MEMBER,
            }

        return True

    def has_object_permission(self, request, view, obj):
        role = self._get_role(
            request.user,
            obj.project,
        )

        if role is None:
            return False

        if request.method in SAFE_METHODS:
            return True

        if view.action == "destroy":
            return role == ProjectMembership.Role.MANAGER

        return role in {
            ProjectMembership.Role.MANAGER,
            ProjectMembership.Role.MEMBER,
        }
