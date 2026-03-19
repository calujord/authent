from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Country, Location, Notification
from .serializers import (
    CountryCreateUpdateSerializer,
    CountryListSerializer,
    CountrySerializer,
    LocationListSerializer,
    LocationSerializer,
)
from .serializers.notification import (
    NotificationListSerializer,
    NotificationSerializer,
)


@extend_schema_view(
    list=extend_schema(description="List locations", tags=["Locations"]),
    create=extend_schema(description="Create new location", tags=["Locations"]),
    retrieve=extend_schema(description="Get location by ID", tags=["Locations"]),
    update=extend_schema(description="Update location", tags=["Locations"]),
    destroy=extend_schema(description="Delete location", tags=["Locations"]),
)
class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for location management."""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "list":
            return LocationListSerializer
        return LocationSerializer

    @extend_schema(description="Get only active locations", tags=["Locations"])
    @action(detail=False, methods=["get"])
    def active(self, request):
        """Endpoint to get only active locations."""
        active_locations = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_locations, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List countries", tags=["Countries"]),
    create=extend_schema(description="Create new country (admin)", tags=["Countries"]),
    retrieve=extend_schema(description="Get country by ID", tags=["Countries"]),
    update=extend_schema(description="Update country (admin)", tags=["Countries"]),
    destroy=extend_schema(description="Delete country (admin)", tags=["Countries"]),
)
class CountryViewSet(viewsets.ModelViewSet):
    """ViewSet for country management with multi-language support."""

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "code_iso2", "phone_code"]
    search_fields = [
        "name",
        "name_en",
        "name_pt",
        "name_fr",
        "name_it",
        "code_iso2",
        "code_iso3",
    ]
    ordering_fields = ["name", "sort_order", "created_at"]
    ordering = ["sort_order", "name"]

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "list":
            return CountryListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CountryCreateUpdateSerializer
        return CountrySerializer

    def get_permissions(self):
        """Override permissions: public read, admin-only write."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        elif self.action in ["list", "retrieve", "active", "by_language"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(description="Get only active countries", tags=["Countries"])
    @action(detail=False, methods=["get"])
    def active(self, request):
        """Endpoint to get only active countries."""
        active_countries = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_countries, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get countries with specific language translation",
        tags=["Countries"],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="by-language/(?P<language>[a-z]{2})",
    )
    def by_language(self, request, language=None):
        """Get countries with specific language preference."""
        if language not in ["es", "en", "pt", "fr", "it"]:
            return Response(
                {"error": "Unsupported language. Use: es, en, pt, fr, it"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        countries = self.get_queryset().filter(is_active=True)

        # Add language to request context
        context = self.get_serializer_context()
        context["language"] = language

        serializer = self.get_serializer(countries, many=True, context=context)
        return Response(serializer.data)

    @extend_schema(description="Get countries by phone code", tags=["Countries"])
    @action(detail=False, methods=["get"])
    def by_phone_code(self, request):
        """Get countries filtered by phone code."""
        phone_code = request.query_params.get("code")
        if not phone_code:
            return Response(
                {"error": "Phone code parameter 'code' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        countries = self.get_queryset().filter(phone_code=phone_code, is_active=True)
        serializer = self.get_serializer(countries, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing user notifications (read-only)."""

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        """Return only notifications for the authenticated user."""
        return Notification.objects.filter(
            user=self.request.user, is_deleted=False
        ).order_by("-created_at")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        return NotificationListSerializer

    @extend_schema(
        description="Mark notification as read",
        request=None,
        responses={200: NotificationSerializer},
        tags=["Notifications"],
    )
    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


