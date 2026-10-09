from django.db import transaction

from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership

from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from apps.activity.models import ActivityLog
from apps.activity.services import log_activity

@transaction.atomic
def create_team(
    *,
    user,
    name,
):
    team = Team.objects.create(
        name=name,
    )

    TeamMembership.objects.create(
        user=user,
        team=team,
        role=TeamMembership.Role.OWNER,
    )

    log_activity(
        actor=user,
        action=ActivityLog.Action.CREATED,
        target=team,
    )

    return team


def get_user_teams(user):
    return Team.objects.filter(
        memberships__user=user
    )


def _get_team_membership(*, user, team):
    return (
        TeamMembership.objects
        .filter(
            user=user,
            team=team,
        )
        .first()
    )


@transaction.atomic
def add_team_member(
    *,
    actor,
    team,
    username,
    role=TeamMembership.Role.MEMBER,
):
    actor_membership = _get_team_membership(
        user=actor,
        team=team,
    )

    if actor_membership is None:
        raise PermissionError(
            "User is not a member of this team."
        )

    if actor_membership.role not in {
        TeamMembership.Role.OWNER,
        TeamMembership.Role.ADMIN,
    }:
        raise PermissionError(
            "Only team owners and admins can add members."
        )

    if role not in {
        TeamMembership.Role.ADMIN,
        TeamMembership.Role.MEMBER,
    }:
        raise ValueError(
            "Invalid team role."
        )

    if (
        actor_membership.role == TeamMembership.Role.ADMIN
        and role != TeamMembership.Role.MEMBER
    ):
        raise PermissionError(
            "Admins can only add members."
        )

    try:
        user = User.objects.get(
            username=username,
        )
    except User.DoesNotExist:
        raise ValueError(
            "User not found."
        )

    if TeamMembership.objects.filter(
        user=user,
        team=team,
    ).exists():
        raise ValueError(
            "User is already a team member."
        )

    membership=TeamMembership.objects.create(
        user=user,
        team=team,
        role=role,
    )

    create_notification(
        recipient=user,
        actor=actor,
        notification_type=(
            Notification.NotificationType.MEMBER_ADDED
        ),
        target=team,
        metadata={
            "team_id": team.id,
            "team_name": team.name,
            "role": membership.role,
        },
    )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.ADDED,
        target=team,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "role": membership.role,
        },
    )

    return membership

@transaction.atomic
def change_team_member_role(
    *,
    actor,
    team,
    member_id,
    role,
):
    actor_membership = _get_team_membership(
        user=actor,
        team=team,
    )

    if actor_membership is None:
        raise PermissionError(
            "User is not a member of this team."
        )

    if actor_membership.role != TeamMembership.Role.OWNER:
        raise PermissionError(
            "Only the team owner can change member roles."
        )

    if role not in {
        TeamMembership.Role.ADMIN,
        TeamMembership.Role.MEMBER,
    }:
        raise ValueError(
            "Invalid team role."
        )

    membership = (
        TeamMembership.objects
        .select_related("user")
        .filter(
            id=member_id,
            team=team,
        )
        .first()
    )

    if membership is None:
        raise ValueError(
            "Team member not found."
        )

    if membership.role == TeamMembership.Role.OWNER:
        raise PermissionError(
            "The team owner role cannot be changed."
        )

    old_role = membership.role

    membership.role = role

    membership.save(
        update_fields=[
            "role",
        ]
    )

    create_notification(
        recipient=membership.user,
        actor=actor,
        notification_type=(
            Notification.NotificationType.ROLE_CHANGED
        ),
        target=team,
        metadata={
            "team_id": team.id,
            "team_name": team.name,
            "old_role": old_role,
            "new_role": membership.role,
        },
    )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.ROLE_CHANGED,
        target=team,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "old_role": old_role,
            "new_role": membership.role,
        },
    )

    return membership


@transaction.atomic
def remove_team_member(
    *,
    actor,
    team,
    member_id,
):
    actor_membership = _get_team_membership(
        user=actor,
        team=team,
    )

    if actor_membership is None:
        raise PermissionError(
            "User is not a member of this team."
        )

    membership = (
        TeamMembership.objects
        .select_related("user")
        .filter(
            id=member_id,
            team=team,
        )
        .first()
    )

    if membership is None:
        raise ValueError(
            "Team member not found."
        )

    if membership.role == TeamMembership.Role.OWNER:
        raise PermissionError(
            "The team owner cannot be removed."
        )

    if (
        actor_membership.role == TeamMembership.Role.ADMIN
        and membership.role != TeamMembership.Role.MEMBER
    ):
        raise PermissionError(
            "Admins can only remove members."
        )

    log_activity(
        actor=actor,
        action=ActivityLog.Action.REMOVED,
        target=team,
        metadata={
            "member_id": membership.user_id,
            "username": membership.user.username,
            "role": membership.role,
        },
    )

    membership.delete()

    return membership
