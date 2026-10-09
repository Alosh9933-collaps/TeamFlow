from rest_framework import serializers

from apps.activity.models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):

    actor_username = serializers.SerializerMethodField()

    target_type = serializers.SerializerMethodField()

    target_id = serializers.IntegerField(
        source="object_id",
        read_only=True,
    )

    class Meta:
        model = ActivityLog

        fields = [
            "id",
            "actor_username",
            "action",
            "target_type",
            "target_id",
            "metadata",
            "created_at",
        ]

        read_only_fields = fields

    def get_actor_username(self, obj) -> str | None:
        if obj.actor is None:
            return None

        return obj.actor.username

    def get_target_type(self, obj) -> str:
        return obj.content_type.model
