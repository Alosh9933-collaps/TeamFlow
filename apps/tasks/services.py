from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from apps.projects.models import ProjectMembership
from apps.tasks.models import Task, TaskClaim

from apps.activity.models import ActivityLog
from apps.activity.services import log_activity

@transaction.atomic
def claim_task(*, task_id, user):
    task = (
        Task.objects
        .select_for_update()
        .select_related("project")
        .get(id=task_id)
    )

    is_project_member = ProjectMembership.objects.filter(
        project=task.project,
        user=user,
    ).exists()

    if not is_project_member:
        raise PermissionError(
            "User must be a project member to claim this task."
        )

    if task.status == Task.Status.DONE:
        raise ValueError(
            "Cannot claim a completed task."
        )

    has_active_claim = TaskClaim.objects.filter(
        task=task,
        user=user,
        released_at__isnull=True,
    ).exists()

    if has_active_claim:
        raise ValueError(
            "User already has an active claim for this task."
        )

    claim = TaskClaim.objects.create(
        task=task,
        user=user,
    )

    if task.status == Task.Status.TODO:
        task.status = Task.Status.PENDING
        task.save(update_fields=["status"])

    return claim

@transaction.atomic
def unclaim_task(*, task_id, user):
    task = (
        Task.objects
        .select_for_update()
        .get(id=task_id)
    )

    if task.status == Task.Status.DONE:
        raise ValueError(
            "Cannot unclaim a completed task."
        )

    claim = (
        TaskClaim.objects
        .select_for_update()
        .filter(
            task=task,
            user=user,
            released_at__isnull=True,
        )
        .first()
    )

    if claim is None:
        raise ValueError(
            "User does not have an active claim for this task."
        )

    claim.released_at = timezone.now()
    claim.save(update_fields=["released_at"])

    has_active_claims = TaskClaim.objects.filter(
        task=task,
        released_at__isnull=True,
    ).exists()

    if not has_active_claims:
        task.status = Task.Status.TODO
        task.save(update_fields=["status"])

    return claim

@transaction.atomic
def complete_task(*, task_id, user):
    task = (
        Task.objects
        .select_for_update()
        .get(id=task_id)
    )

    if task.status == Task.Status.DONE:
        raise ValueError(
            "Task is already completed."
        )

    claim = (
        TaskClaim.objects
        .select_for_update()
        .filter(
            task=task,
            user=user,
            released_at__isnull=True,
            completed_at__isnull=True,
        )
        .first()
    )

    if claim is None:
        raise PermissionError(
            "User does not have an active claim for this task."
        )

    claim.completed_at = timezone.now()
    claim.save(update_fields=["completed_at"])

    task.status = Task.Status.DONE
    task.save(update_fields=["status"])

    log_activity(
        actor=user,
        action=ActivityLog.Action.COMPLETED,
        target=task,
        metadata={
            "task_id": task.id,
        },
    )

    create_notification(
        recipient=claim.user,
        actor=user,
        notification_type=Notification.NotificationType.TASK_COMPLETED,
        target=task,
        metadata={
            "task_id": task.id,
            "task_title": task.title,
        },
    )

    return claim
