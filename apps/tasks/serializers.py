from rest_framework import serializers

from apps.tasks.models import TaskClaim, Task


class TaskClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskClaim
        fields = [
            "id",
            "task",
            "user",
            "claimed_at",
            "completed_at",
            "released_at",
        ]
        read_only_fields = [
            "id",
            "task",
            "user",
            "claimed_at",
            "completed_at",
            "released_at",
        ]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "tags",
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
