from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import PasswordReset, TermsAndConditions, User
from .serializers import (
    AcceptTermsSerializer,
    CurrentTermsSerializer,
    # Auth serializers
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    # Password serializers
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    # Terms serializers
    TermsAndConditionsSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    # Registration serializers
    UserRegistrationSerializer,
    UserTermsAcceptanceSerializer,
    UserUpdateSerializer,
)


@extend_schema_view(
    post=extend_schema(
        description="Register a new user account", tags=["Authentication"]
    )
)
class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Create user and return success message."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully",
                "user_id": user.id,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        description="Login with email and password", tags=["Authentication"]
    )
)
class UserLoginView(TokenObtainPairView):
    """User login endpoint with JWT tokens."""

    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    get=extend_schema(description="Get user profile", tags=["Authentication"]),
    put=extend_schema(description="Update user profile", tags=["Authentication"]),
    patch=extend_schema(
        description="Partially update user profile", tags=["Authentication"]
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        description="Request password reset - sends PIN to email",
        tags=["Authentication"],
    )
)
class PasswordResetRequestView(APIView):
    """Password reset request endpoint."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Send password reset PIN to user email."""
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
        tags=["Authentication"],
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
        description="Reset password with verified PIN and hash", tags=["Authentication"]
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
            {"message": "Password reset successfully", "user_id": user.id},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        description="Verify PIN for Flutter app (simplified endpoint)",
        tags=["Authentication"],
    )
)
class FlutterPinCheckView(APIView):
    """Simple PIN verification endpoint for Flutter app."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Verify PIN using only email and code (no hash_token required)."""
        from .serializers import FlutterPinVerifySerializer

        serializer = FlutterPinVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "PIN verified successfully", "valid": True},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        description="Get current active terms and conditions", tags=["Authentication"]
    )
)
class TermsAndConditionsView(generics.ListAPIView):
    """Get current active terms and conditions."""

    serializer_class = TermsAndConditionsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Return only active terms."""
        return TermsAndConditions.objects.filter(is_active=True)


@extend_schema(
    description="Check if user needs to accept new terms", tags=["Authentication"]
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_terms_acceptance(request):
    """Check if user needs to accept latest terms."""
    try:
        latest_terms = TermsAndConditions.objects.get(is_active=True)

        # Check if user has accepted latest terms
        has_accepted = request.user.terms_acceptances.filter(
            terms=latest_terms
        ).exists()

        return Response(
            {
                "needs_acceptance": not has_accepted,
                "latest_version": latest_terms.version,
                "terms_content": latest_terms.content if not has_accepted else None,
            }
        )

    except TermsAndConditions.DoesNotExist:
        return Response({"needs_acceptance": False, "message": "No active terms found"})


@extend_schema(
    description="Accept current terms and conditions", tags=["Authentication"]
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def accept_terms(request):
    """Accept current active terms and conditions."""
    version = request.data.get("version")

    if not version:
        return Response(
            {"error": "Version is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        terms = TermsAndConditions.objects.get(version=version, is_active=True)

        # Check if already accepted
        if request.user.terms_acceptances.filter(terms=terms).exists():
            return Response({"message": "Terms already accepted"})

        # Create acceptance record
        from .models import UserTermsAcceptance

        UserTermsAcceptance.objects.create(
            user=request.user, terms=terms, ip_address=request.META.get("REMOTE_ADDR")
        )

        return Response({"message": "Terms accepted successfully"})

    except TermsAndConditions.DoesNotExist:
        return Response(
            {"error": "Invalid or inactive terms version"},
            status=status.HTTP_400_BAD_REQUEST,
        )
