from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.activity.models import ActivityLog
from apps.projects.models import Project
from apps.tasks.models import Task


def log_activity(
    *,
    actor,
    action,
    target,
    metadata=None,
):
    content_type = ContentType.objects.get_for_model(
        target
    )

    return ActivityLog.objects.create(
        actor=actor,
        action=action,
        content_type=content_type,
        object_id=target.pk,
        metadata=metadata or {},
    )


def get_project_activity(*, project):
    project_content_type = ContentType.objects.get_for_model(
        Project
    )

    task_content_type = ContentType.objects.get_for_model(
        Task
    )

    return (
        ActivityLog.objects
        .filter(
            Q(
                content_type=project_content_type,
                object_id=project.id,
            )
            |
            Q(
                content_type=task_content_type,
                object_id__in=Task.objects.filter(
                    project=project
                ).values("id"),
            )
        )
        .select_related("actor")
    )
