"""Serializers for file upload management."""

from rest_framework import serializers


class AvatarUploadSerializer(serializers.Serializer):
    """Serializer for avatar upload."""

    avatar = serializers.ImageField(
        required=True,
        help_text="Avatar image file (JPEG, PNG, GIF)",
        allow_empty_file=False,
    )

    def validate_avatar(self, value):
        """Validate avatar file."""
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Avatar file size must be less than 5MB")

        # Check file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )

        return value


class AvatarResponseSerializer(serializers.Serializer):
    """Serializer for avatar upload response."""

    avatar = serializers.URLField(help_text="URL of the uploaded avatar")
    message = serializers.CharField(help_text="Success message")
