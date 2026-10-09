from django.conf import settings
from django.db import models


class Project(models.Model):
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        MEMBER = "MEMBER", "Member"
        VIEWER = "VIEWER", "Viewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"],
                name="unique_user_project_membership",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.role}"

class ProjectJoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_join_requests",
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    requested_at = models.DateTimeField(auto_now_add=True)

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_project_join_requests",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"],
                condition=models.Q(status="PENDING"),
                name="unique_pending_project_join_request",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.project.name} - "
            f"{self.status}"
        )
