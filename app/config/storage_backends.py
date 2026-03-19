"""
Custom storage backends for S3 with proper location configuration.
"""

from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """S3 storage backend for media files."""

    location = "media"
    file_overwrite = False
    default_acl = "private"


class StaticStorage(S3Boto3Storage):
    """S3 storage backend for static files."""

    location = "static"
    default_acl = "private"  # Bucket has Block Public Access enabled
