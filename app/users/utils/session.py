"""Utilities for session management."""

import hashlib
from datetime import datetime, timedelta, timezone as dt_timezone

from django.utils import timezone
from user_agents import parse


def parse_user_agent(user_agent_string):
    """Parse user agent string to extract device information."""
    ua = parse(user_agent_string)

    # Determine device type
    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return {
        "device_type": device_type,
        "os_name": ua.os.family,
        "os_version": ua.os.version_string,
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
    }


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def hash_token(token):
    """Create a hash of the refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user, access_token, refresh_token, request):
    """
    Create a new user session record.

    Args:
        user: User instance
        access_token: JWT access token object (decoded)
        refresh_token: Refresh token string
        request: Django request object

    Returns:
        UserSession instance
    """
    from users.models.session import UserSession

    # Get device information
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    device_info = parse_user_agent(user_agent)
    ip_address = get_client_ip(request)

    # Get token expiration
    exp_timestamp = access_token.get("exp")
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=dt_timezone.utc)

    # Create session
    session = UserSession.objects.create(
        user=user,
        jti=access_token.get("jti"),
        refresh_token_hash=hash_token(refresh_token),
        device_type=device_info["device_type"],
        os_name=device_info["os_name"],
        os_version=device_info["os_version"],
        browser=device_info["browser"],
        browser_version=device_info["browser_version"],
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )

    return session


def update_session_activity(jti):
    """Update last activity timestamp for a session."""
    from users.models.session import UserSession

    UserSession.objects.filter(jti=jti, is_active=True).update(
        last_activity=timezone.now()
    )
