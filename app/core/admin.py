from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Country, Location, Notification

# Try to import GIS admin classes, fallback to regular
# ModelAdmin if not available


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    """Admin configuration for Location model."""

    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = [
        (
            "Basic Information",
            {"fields": ("name", "description", "is_active")},
        ),
        ("Location", {"fields": ("point",), "classes": ["collapse"]}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ["collapse"]},
        ),
    ]


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    """Admin configuration for Country model with multi-language support."""

    list_display = [
        "name",
        "code_iso2",
        "phone_code",
        "currency_code",
        "is_active",
        "sort_order",
    ]
    list_filter = ["is_active", "currency_code"]
    search_fields = [
        "name",
        "name_en",
        "name_pt",
        "name_fr",
        "name_it",
        "code_iso2",
        "code_iso3",
    ]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["sort_order", "name"]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": (
                    ("name", "is_active"),
                    ("code_iso2", "code_iso3", "numeric_code"),
                    ("phone_code", "currency_code"),
                    "sort_order",
                )
            },
        ),
        (
            "Multi-Language Names",
            {
                "fields": (("name_en", "name_pt"), ("name_fr", "name_it")),
                "classes": ["collapse"],
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ["collapse"]},
        ),
    ]

    def get_queryset(self, request):
        """Include soft-deleted records for admin."""
        return self.model.all_objects.all()


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """Admin configuration for Notification model."""

    list_display = [
        "title",
        "user",
        "notification_type",
        "is_read",
        "created_at",
    ]
    list_filter = [
        "notification_type",
        "is_read",
        "created_at",
    ]
    search_fields = ["title", "message", "user__email", "user__first_name"]
    readonly_fields = ["id", "read_at", "created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "user",
                    "title",
                    "message",
                    "notification_type",
                    "url",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    ("is_read", "read_at"),
                    "is_active",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata", "created_at", "updated_at"),
                "classes": ["collapse"],
            },
        ),
    )

    def get_queryset(self, request):
        """Include soft-deleted records for admin."""
        return self.model.all_objects.all()
