from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from apps.notifications.models import Notification


def create_notification(
    *,
    recipient,
    notification_type,
    target,
    actor=None,
    metadata=None,
):
    content_type = ContentType.objects.get_for_model(
        target
    )

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        content_type=content_type,
        object_id=target.pk,
        metadata=metadata or {},
    )

def mark_notification_as_read(
    *,
    notification,
    user,
):
    if notification.recipient_id != user.id:
        raise PermissionError(
            "You cannot modify another user's notification."
        )

    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(
            update_fields=[
                "read_at",
            ]
        )

    return notification

def get_user_notifications(*, user, unread_only=False):
    notifications = (
        Notification.objects
        .filter(recipient=user)
        .select_related(
            "recipient",
            "actor",
            "content_type",
        )
    )

    if unread_only:
        notifications = notifications.filter(
            read_at__isnull=True
        )

    return notifications


def mark_all_notifications_as_read(*, user):
    return (
        Notification.objects
        .filter(
            recipient=user,
            read_at__isnull=True,
        )
        .update(
            read_at=timezone.now()
        )
    )
