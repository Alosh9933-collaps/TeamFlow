from django.db import transaction
from django.utils import timezone

from apps.activity.models import ActivityLog
from apps.activity.services import log_activity
from apps.projects.models import (
    Project,
    ProjectJoinRequest,
    ProjectMembership,
)

from apps.teams.models import TeamMembership

from apps.notifications.models import Notification
from apps.notifications.services import create_notification

@transaction.atomic
def approve_project_join_request(
    *,
    join_request_id,
    reviewer,
):
    join_request = (
        ProjectJoinRequest.objects
        .select_for_update()
        .select_related("project__team", "user")
        .get(id=join_request_id)
    )

    if join_request.status != ProjectJoinRequest.Status.PENDING:
        raise ValueError("Join request is not pending.")

    is_manager = ProjectMembership.objects.filter(
        project=join_request.project,
        user=reviewer,
        role=ProjectMembership.Role.MANAGER,
    ).exists()

    if not is_manager:
        raise PermissionError(
            "Only a project manager can approve join requests."
        )

    membership, created = ProjectMembership.objects.get_or_create(
        user=join_request.user,
        project=join_request.project,
        defaults={
            "role": ProjectMembership.Role.MEMBER,
        },
    )

    if not created:
        raise ValueError("User is already a project member.")

    join_request.status = ProjectJoinRequest.Status.APPROVED
    join_request.reviewed_by = reviewer
    join_request.reviewed_at = timezone.now()
    join_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
        ]
    )

    create_notification(
        recipient=join_request.user,
        actor=reviewer,
        notification_type=(
            Notification.NotificationType
            .JOIN_REQUEST_APPROVED
        ),
        target=join_request.project,
        metadata={
            "project_id": join_request.project.id,
            "project_name": join_request.project.name,
        },
    )

    return membership


@transaction.atomic
def create_project_join_request(*, user, project):
    is_team_member = TeamMembership.objects.filter(
        user=user,
        team=project.team,
    ).exists()

    if not is_team_member:
        raise PermissionError(
            "User must be a team member to request project access."
        )

    is_project_member = ProjectMembership.objects.filter(
        user=user,
        project=project,
    ).exists()

    if is_project_member:
        raise ValueError(
            "User is already a project member."
        )

    has_pending_request = ProjectJoinRequest.objects.filter(
        user=user,
        project=project,
        status=ProjectJoinRequest.Status.PENDING,
    ).exists()

    if has_pending_request:
        raise ValueError(
            "User already has a pending join request."
        )

    return ProjectJoinRequest.objects.create(
        user=user,
        project=project,
    )
@transaction.atomic
def create_project(
    *,
    user,
    team,
    name,
    description="",
):
    team_membership = TeamMembership.objects.filter(
        user=user,
        team=team,
    ).first()

    if not team_membership:
        raise PermissionError(
            "User must be a team member to create a project."
        )

    if team_membership.role not in {
        TeamMembership.Role.OWNER,
        TeamMembership.Role.ADMIN,
    }:
        raise PermissionError(
            "Only team owners and admins can create projects."
        )

    project = Project.objects.create(
        team=team,
        name=name,
        description=description,
        created_by=user,
    )

    ProjectMembership.objects.create(
        user=user,
        project=project,
        role=ProjectMembership.Role.MANAGER,
    )

    log_activity(
        actor=user,
        action=ActivityLog.Action.CREATED,
        target=project,
    )
    return project

@transaction.atomic
def add_project_member(
    *,
    actor,
    project,
    username,
    role=ProjectMembership.Role.MEMBER,
):
    actor_project_role = ProjectMembership.objects.filter(
        user=actor,
        project=project,
    ).values_list(
        "role",
        flat=True,
    ).first()

    actor_team_role = TeamMembership.objects.filter(
        user=actor,
        team=project.team,
    ).values_list(
        "role",
        flat=True,
    ).first()

    if (
        actor_project_role != ProjectMembership.Role.MANAGER
        and actor_team_role not in {
            TeamMembership.Role.OWNER,
            TeamMembership.Role.ADMIN,
        }
    ):
        raise PermissionError(
            "You cannot manage project members."
        )

    if role not in {
        ProjectMembership.Role.MEMBER,
        ProjectMembership.Role.VIEWER,
    }:
        raise ValueError(
            "Invalid project role."
        )

    from apps.accounts.models import User

    try:
        user = User.objects.get(
            username=username
        )
    except User.DoesNotExist:
        raise ValueError(
            "User not found."
        )

    if ProjectMembership.objects.filter(
        user=user,
        project=project,
    ).exists():
        raise ValueError(
            "User is already a project member."
        )

    membership = ProjectMembership.objects.create(
    user=user,
    project=project,
    role=role,
    )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.ADDED,
        target=project,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "role": membership.role,
        },
    )

    return membership

@transaction.atomic
def change_project_member_role(
    *,
    actor,
    project,
    member_id,
    role,
):
    actor_project_role = ProjectMembership.objects.filter(
        user=actor,
        project=project,
    ).values_list(
        "role",
        flat=True,
    ).first()

    actor_team_role = TeamMembership.objects.filter(
        user=actor,
        team=project.team,
    ).values_list(
        "role",
        flat=True,
    ).first()

    if (
        actor_project_role != ProjectMembership.Role.MANAGER
        and actor_team_role not in {
            TeamMembership.Role.OWNER,
            TeamMembership.Role.ADMIN,
        }
    ):
        raise PermissionError(
            "You cannot manage project members."
        )

    if role not in {
        ProjectMembership.Role.MEMBER,
        ProjectMembership.Role.VIEWER,
    }:
        raise ValueError(
            "Invalid project role."
        )

    membership = (
        ProjectMembership.objects
        .filter(
            id=member_id,
            project=project,
        )
        .first()
    )

    if membership is None:
        raise ValueError(
            "Project member not found."
        )

    if membership.role == ProjectMembership.Role.MANAGER:
        raise PermissionError(
            "Project manager role cannot be changed."
        )

    old_role = membership.role

    membership.role = role

    membership.save(
        update_fields=[
            "role",
        ],
    )

    create_notification(
        recipient=membership.user,
        actor=actor,
        notification_type=Notification.NotificationType.ROLE_CHANGED,
        target=project,
        metadata={
            "project_id": project.id,
            "project_name": project.name,
            "old_role": old_role,
            "new_role": membership.role,
        },
    )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.ROLE_CHANGED,
        target=project,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "old_role": old_role,
            "new_role": membership.role,
        },
    )

    return membership

@transaction.atomic
def remove_project_member(
    *,
    actor,
    project,
    member_id,
):
    actor_project_role = ProjectMembership.objects.filter(
        user=actor,
        project=project,
    ).values_list(
        "role",
        flat=True,
    ).first()

    actor_team_role = TeamMembership.objects.filter(
        user=actor,
        team=project.team,
    ).values_list(
        "role",
        flat=True,
    ).first()

    if (
        actor_project_role != ProjectMembership.Role.MANAGER
        and actor_team_role not in {
            TeamMembership.Role.OWNER,
            TeamMembership.Role.ADMIN,
        }
    ):
        raise PermissionError(
            "You cannot manage project members."
        )

    membership = (
        ProjectMembership.objects
        .filter(
            id=member_id,
            project=project,
        )
        .first()
    )

    if membership is None:
        raise ValueError(
            "Project member not found."
        )

    if membership.role == ProjectMembership.Role.MANAGER:
        raise PermissionError(
            "Project manager cannot be removed."
        )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.REMOVED,
        target=project,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "role": membership.role,
        },
    )

    create_notification(
        recipient=membership.user,
        actor=actor,
        notification_type=Notification.NotificationType.MEMBER_REMOVED,
        target=project,
        metadata={
            "project_id": project.id,
            "project_name": project.name,
            "member_id": membership.user.id,
            "username": membership.user.username,
            "role": membership.role,
        },
    )

    membership.delete()

    return True
