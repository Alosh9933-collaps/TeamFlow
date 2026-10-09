from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User(
            **validated_data,
            is_active=False,
        )

        user.set_password(password)
        user.save()

        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    new_password_confirm = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        if (
            attrs["new_password"]
            != attrs["new_password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "new_password_confirm": (
                        "Passwords do not match."
                    )
                }
            )

        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "is_active",
        ]
