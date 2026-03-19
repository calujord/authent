"""Serializers for Notification model."""

from rest_framework import serializers

from core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Full serializer for Notification model."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(
        source="user.get_full_name", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "title",
            "message",
            "notification_type",
            "is_read",
            "read_at",
            "url",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_name",
            "read_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create notification with user from request."""
        # If user is not provided, use the authenticated user
        if "user" not in validated_data:
            validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for notification list."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "is_read",
            "url",
            "created_at",
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications."""

    class Meta:
        model = Notification
        fields = [
            "title",
            "message",
            "notification_type",
            "url",
            "metadata",
        ]

    def create(self, validated_data):
        """Create notification for the authenticated user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
