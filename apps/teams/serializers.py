from rest_framework import serializers

from apps.teams.models import Team, TeamMembership


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team

        fields = [
            "id",
            "name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class TeamMembershipSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = TeamMembership

        fields = [
            "id",
            "user",
            "username",
            "team",
            "role",
            "joined_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "joined_at",
        ]


class AddTeamMemberSerializer(serializers.Serializer):

    username = serializers.CharField()

    role = serializers.ChoiceField(
        choices=[
            TeamMembership.Role.ADMIN,
            TeamMembership.Role.MEMBER,
        ],
        default=TeamMembership.Role.MEMBER,
    )


class ChangeTeamMemberRoleSerializer(serializers.Serializer):

    role = serializers.ChoiceField(
        choices=[
            TeamMembership.Role.ADMIN,
            TeamMembership.Role.MEMBER,
        ],
    )
