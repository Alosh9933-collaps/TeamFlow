from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        MEMBER_ADDED = "MEMBER_ADDED", "Member added"
        ROLE_CHANGED = "ROLE_CHANGED", "Role changed"
        JOIN_REQUEST_APPROVED = (
            "JOIN_REQUEST_APPROVED",
            "Join request approved",
        )
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task assigned"
        TASK_COMPLETED = "TASK_COMPLETED", "Task completed"
        MEMBER_REMOVED = "MEMBER_REMOVED", "Member removed"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveBigIntegerField()

    target = GenericForeignKey(
        "content_type",
        "object_id",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.recipient.username} - "
            f"{self.notification_type}"
        )
