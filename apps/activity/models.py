from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        UPDATED = "UPDATED", "Updated"
        DELETED = "DELETED", "Deleted"
        ADDED = "ADDED", "Added"
        REMOVED = "REMOVED", "Removed"
        ROLE_CHANGED = "ROLE_CHANGED", "Role changed"
        COMPLETED = "COMPLETED", "Completed"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activity_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.actor} - "
            f"{self.action} - "
            f"{self.target}"
        )
