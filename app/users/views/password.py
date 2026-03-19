from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    SimplePasswordResetSerializer,
    SimplePinVerifySerializer,
)


@extend_schema_view(
    post=extend_schema(
        description="Request password reset PIN via email", tags=["Password Reset"]
    )
)
class PasswordResetRequestView(APIView):
    """Request password reset via email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Send password reset PIN to user's email."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        return Response(
            {
                "message": "Reset PIN sent to your email",
                "hash_token": result["hash_token"],
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        description="Verify PIN and hash token for password reset",
        tags=["Password Reset"],
    )
)
class PasswordResetVerifyView(APIView):
    """Verify PIN for password reset."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify PIN and hash combination."""
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "PIN verified successfully", "valid": True},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        description="Reset password with verified PIN and hash", tags=["Password Reset"]
    )
)
class PasswordResetConfirmView(APIView):
    """Confirm password reset with new password."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Reset password with verified credentials."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {"message": "Password reset successfully", "user_id": str(user.id)},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        description="Change password for authenticated user OR reset with PIN",
        tags=["Password Management"],
    )
)
class PasswordChangeView(APIView):
    """Change password for authenticated user OR reset password with PIN."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Change user password."""
        # Check if it's a password reset with PIN (email + code + newPassword)
        if "code" in request.data and "email" in request.data:
            # Password reset with PIN
            serializer = SimplePasswordResetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            return Response(
                {"message": "Password reset successfully", "user_id": str(user.id)},
                status=status.HTTP_200_OK,
            )
        else:
            # Regular password change for authenticated user
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            serializer = PasswordChangeSerializer(data=request.data, user=request.user)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK,
            )


@extend_schema_view(
    post=extend_schema(
        description="Simple PIN verification with email and code only",
        tags=["Password Reset"],
    )
)
class SimplePinCheckView(APIView):
    """Simple PIN verification endpoint."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify PIN using only email and code."""
        serializer = SimplePinVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "PIN verified successfully", "valid": True},
            status=status.HTTP_200_OK,
        )
