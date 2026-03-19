"""Views for file upload management."""

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers.upload import AvatarResponseSerializer, AvatarUploadSerializer
from core.utils.s3_signed_url import get_avatar_url


class UserAvatarUploadView(APIView):
    """
    Upload avatar for authenticated user.

    POST: Upload a new avatar image
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AvatarUploadSerializer

    @extend_schema(
        description="Upload avatar image for the authenticated user",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "avatar": {
                        "type": "string",
                        "format": "binary",
                        "description": "Avatar image file (max 5MB, JPEG/PNG/GIF/WEBP)",
                    }
                },
                "required": ["avatar"],
            }
        },
        responses={
            200: AvatarResponseSerializer,
            400: {"description": "Validation error"},
            401: {"description": "Authentication required"},
        },
        tags=["Upload"],
    )
    def post(self, request):
        """Upload user avatar."""
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the uploaded file
        avatar_file = serializer.validated_data["avatar"]

        # Delete old avatar if exists (optional, to avoid S3 clutter)
        if request.user.avatar:
            try:
                request.user.avatar.delete(save=False)
            except Exception:
                pass  # If deletion fails, continue anyway

        # Save new avatar
        request.user.avatar = avatar_file
        request.user.save()

        # Generate signed URL with 30 minutes expiration
        avatar_url = get_avatar_url(request.user.avatar, expiration=1800)

        return Response(
            {"avatar": avatar_url, "message": "Avatar uploaded successfully"},
            status=status.HTTP_200_OK,
        )
