from django.conf import settings
from django.db import models


class Tag(models.Model):
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="tags",
    )

    name = models.CharField(
        max_length=50,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"],
                name="unique_tag_name_per_team",
            )
        ]

    def __str__(self):
        return self.name

class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        PENDING = "PENDING", "Pending"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="tasks",
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_deleted = models.BooleanField(
        default=False,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

class TaskClaim(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="claims",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_claims",
    )

    claimed_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    released_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "user"],
                condition=models.Q(released_at__isnull=True),
                name="unique_active_task_claim",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"
