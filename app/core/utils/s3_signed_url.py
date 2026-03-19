"""Utility for generating signed S3 URLs."""

import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_signed_url(file_path, expiration=1800):
    """
    Generate a presigned URL for an S3 object.

    Args:
        file_path: Path to the file in S3 (e.g., 'avatars/user_123.jpg')
        expiration: Time in seconds for the URL to remain valid (default: 1800 = 30 minutes)

    Returns:
        str: Presigned URL or None if generation fails
    """
    if not file_path:
        return None

    # Clean up: if a full S3 URL was passed, extract just the path
    if file_path.startswith("http"):
        from urllib.parse import unquote, urlparse

        parsed = urlparse(unquote(file_path))
        # Extract path from S3 URL, remove leading slash
        clean_path = parsed.path.lstrip("/")
        # Remove bucket name prefix if present
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if clean_path.startswith(f"{bucket_name}/"):
            clean_path = clean_path[len(f"{bucket_name}/") :]
        file_path = clean_path
        logger.info(f"Cleaned S3 URL to path: {file_path}")

    # Check if S3 is configured
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        # If S3 is not configured, return the regular media URL
        logger.warning("AWS credentials not configured, returning local media URL")
        return settings.MEDIA_URL + file_path

    try:
        # Create S3 client with regional endpoint
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=f"https://s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

        # The file_path from Django includes the upload_to path (e.g., 'avatars/file.jpg')
        # When using MediaStorage with location='media', we need to add the prefix
        # if it's not already present
        s3_key = file_path

        # Add media prefix if not present and storage uses MediaStorage
        if hasattr(settings, "AWS_MEDIA_LOCATION") and settings.AWS_MEDIA_LOCATION:
            if not file_path.startswith(f"{settings.AWS_MEDIA_LOCATION}/"):
                s3_key = f"{settings.AWS_MEDIA_LOCATION}/{file_path}"

        bucket = settings.AWS_STORAGE_BUCKET_NAME

        logger.info(f"Generating signed URL for bucket={bucket}, key={s3_key}")

        # Generate presigned URL
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiration,
        )

        logger.info(f"Successfully generated signed URL for {s3_key}")
        return response

    except ClientError as e:
        logger.error(f"ClientError generating signed URL for {file_path}: {e}")
        logger.error(f"Bucket: {settings.AWS_STORAGE_BUCKET_NAME}, Key: {s3_key}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating signed URL for {file_path}: {e}")
        return None


def get_avatar_url(field_file, expiration=1800):
    """
    Get signed URL for an avatar ImageField or FileField.

    Args:
        field_file: Django ImageField/FileField instance
        expiration: Time in seconds for the URL to remain valid (default: 1800 = 30 minutes)

    Returns:
        str: Signed URL or None if file doesn't exist
    """
    if not field_file:
        return None

    try:
        # Get the file path/name
        file_path = field_file.name
        logger.info(f"Getting avatar URL for file_path: {file_path}")

        # If using S3, always generate signed URL for security
        if (
            hasattr(settings, "DEFAULT_FILE_STORAGE")
            and "S3" in settings.DEFAULT_FILE_STORAGE
        ):
            logger.info(f"S3 configured, generating signed URL for security")
            return generate_signed_url(file_path, expiration)

        # Otherwise return regular URL
        logger.info(f"S3 not configured, returning regular URL")
        return field_file.url

    except Exception as e:
        logger.error(f"Error getting avatar URL: {e}")
        return None
