"""Views for user session management."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models.session import UserSession
from users.serializers.session import CreateUserSessionSerializer, UserSessionSerializer


class UserSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user sessions."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return CreateUserSessionSerializer
        return UserSessionSerializer

    def get_queryset(self):
        """Return only sessions for the authenticated user."""
        return UserSession.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-last_activity")

    def create(self, request, *args, **kwargs):
        """Create a new session with device information from client."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save()

        # Return the created session with full information
        output_serializer = UserSessionSerializer(session)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"])
    def revoke(self, request, pk=None):
        """
        Revoke a specific session.

        Cannot revoke the current session.
        """
        session = self.get_object()

        # Prevent revoking current session
        if session.is_current_device:
            return Response(
                {"error": "Cannot revoke current session. Use logout instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.revoke()

        return Response(
            {"message": "Session revoked successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"])
    def revoke_all(self, request):
        """
        Revoke all sessions except the current one.
        """
        current_jti = request.auth.get("jti") if hasattr(request, "auth") else None

        # Get all sessions except current
        sessions = self.get_queryset().exclude(jti=current_jti)

        count = sessions.count()
        sessions.update(is_active=False)

        return Response(
            {
                "message": f"{count} session(s) revoked successfully",
                "revoked_count": count,
            },
            status=status.HTTP_200_OK,
        )
