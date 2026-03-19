import jwt
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers import CustomTokenObtainPairSerializer, UserProfileSerializer


@extend_schema_view(
    post=extend_schema(
        description="Login with email and password", tags=["Authentication"]
    )
)
class UserLoginView(TokenObtainPairView):
    """User login endpoint with JWT tokens."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Login user and create session record."""

        from users.utils.session import create_session

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Get tokens from response
            access_token_str = response.data.get("access")
            refresh_token_str = response.data.get("refresh")

            # Decode access token to get JTI and user info
            try:
                access_token = jwt.decode(
                    access_token_str,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                )

                # Get user
                from users.models import User

                user = User.objects.get(id=access_token["user_id"])

                # Create session record
                create_session(user, access_token, refresh_token_str, request)

            except Exception as e:
                # Log error but don't fail the login
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create session record: {e}")

        return response


@extend_schema_view(
    get=extend_schema(description="Get current user profile", tags=["Authentication"]),
    put=extend_schema(
        description="Update current user profile", tags=["Authentication"]
    ),
    patch=extend_schema(
        description="Partially update current user profile",
        tags=["Authentication"],
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return current authenticated user."""
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        description="Logout user and blacklist tokens", tags=["Authentication"]
    )
)
class UserLogoutView(APIView):
    """User logout endpoint."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting the refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from rest_framework_simplejwt.tokens import RefreshToken

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": "Something went wrong during logout"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema_view(
    get=extend_schema(
        description="Verify if user token is still valid",
        tags=["Authentication"],
    )
)
class TokenVerifyView(APIView):
    """Token verification endpoint."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Verify that the token is still valid."""
        user = request.user

        return Response(
            {
                "valid": True,
                "user": UserProfileSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
