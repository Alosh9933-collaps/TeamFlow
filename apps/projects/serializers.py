from rest_framework import serializers

from apps.projects.models import (
    Project,
    ProjectMembership,
    ProjectJoinRequest,
)

class ProjectJoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectJoinRequest
        fields = [
            "id",
            "project",
            "status",
            "requested_at",
            "reviewed_at",
            "reviewed_by",
        ]
        read_only_fields = [
            "id",
            "status",
            "requested_at",
            "reviewed_at",
            "reviewed_by",
        ]

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "team",
            "name",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]

class ProjectMembershipSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = ProjectMembership

        fields = [
            "id",
            "user",
            "username",
            "project",
            "role",
            "joined_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "joined_at",
        ]


class AddProjectMemberSerializer(serializers.Serializer):

    username = serializers.CharField()

    role = serializers.ChoiceField(
        choices=[
            ProjectMembership.Role.MEMBER,
            ProjectMembership.Role.VIEWER,
        ],
        default=ProjectMembership.Role.MEMBER,
    )


class ChangeProjectMemberRoleSerializer(serializers.Serializer):

    role = serializers.ChoiceField(
        choices=[
            ProjectMembership.Role.MEMBER,
            ProjectMembership.Role.VIEWER,
        ],
    )
