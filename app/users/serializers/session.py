"""Serializers for user session management."""

from rest_framework import serializers

from users.models.session import UserSession


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user session information."""

    is_current = serializers.SerializerMethodField()
    device_info = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    application_name = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            "id",
            "device_name",
            "device_type",
            "device_info",
            "location",
            "ip_address",
            "application_name",
            "created_at",
            "last_activity",
            "expires_at",
            "is_active",
            "is_current",
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        return obj.is_current_device

    def get_application_name(self, obj):
        if obj.api_key_id:
            return obj.api_key.application.name
        return None

    def get_device_info(self, obj):
        parts = []
        if obj.os_name:
            os_info = obj.os_name
            if obj.os_version:
                os_info += f" {obj.os_version}"
            parts.append(os_info)

        if obj.browser:
            browser_info = obj.browser
            if obj.browser_version:
                browser_info += f" {obj.browser_version}"
            parts.append(browser_info)

        return " • ".join(parts) if parts else obj.user_agent[:50]

    def get_location(self, obj):
        parts = []
        if obj.city:
            parts.append(obj.city)
        if obj.country:
            parts.append(obj.country)
        return ", ".join(parts) if parts else None


class CreateUserSessionSerializer(serializers.ModelSerializer):
    """Serializer for creating a new session with device information from client."""

    class Meta:
        model = UserSession
        fields = [
            "jti",
            "refresh_token_hash",
            "device_name",
            "device_type",
            "os_name",
            "os_version",
            "browser",
            "browser_version",
            "user_agent",
            "ip_address",
            "country",
            "city",
            "expires_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if request:
            if hasattr(request, "user"):
                attrs["user"] = request.user
            if hasattr(request, "api_key") and request.api_key is not None:
                attrs["api_key"] = request.api_key
        return attrs

    def create(self, validated_data):
        validated_data["is_active"] = True
        return super().create(validated_data)
