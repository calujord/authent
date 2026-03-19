"""
Firebase Cloud Messaging (FCM) Push Notifications Service.

This module provides functionality to send push notifications to mobile
and web clients using Firebase Cloud Messaging.

Configuration required in settings:
    FIREBASE_CREDENTIALS_PATH: Path to Firebase service account JSON file
    or
    FIREBASE_CREDENTIALS: Dict with Firebase credentials

Example usage:
    from core.services.notifications import NotificationService

    # Send to single user
    NotificationService.send_to_user(
        user_id=123,
        title="Nueva cita",
        body="Tu cita es mañana a las 10:00",
        data={"appointment_id": "456"}
    )

    # Send to multiple users
    NotificationService.send_to_users(
        user_ids=[123, 456, 789],
        title="Promoción especial",
        body="20% de descuento en todos los servicios"
    )
"""

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization
_firebase_app = None


def _get_firebase_app():
    """
    Initialize and return Firebase Admin app.

    Uses lazy initialization to avoid import errors when Firebase
    credentials are not configured.

    Priority order:
    1. FIREBASE_CREDENTIALS_PATH (path to JSON file)
    2. FIREBASE_CREDENTIALS_JSON (JSON string in env variable)
    3. FIREBASE_CREDENTIALS (dict in settings)
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized
        try:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app
        except ValueError:
            pass  # App not initialized yet

        cred = None

        # Option 1: Path to JSON file
        cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
        if cred_path and cred_path.strip():
            cred = credentials.Certificate(cred_path)
            logger.info("Firebase initialized from file: %s", cred_path)

        # Option 2: JSON string from environment variable
        if cred is None:
            cred_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", None)
            if not cred_json and hasattr(settings, "env"):
                cred_json = settings.env("FIREBASE_CREDENTIALS_JSON", default="")
            if cred_json and cred_json.strip():
                cred_data = json.loads(cred_json)
                cred = credentials.Certificate(cred_data)
                logger.info("Firebase initialized from JSON env variable")

        # Option 3: Dict directly in settings
        if cred is None:
            cred_data = getattr(settings, "FIREBASE_CREDENTIALS", None)
            if cred_data:
                if isinstance(cred_data, str):
                    cred_data = json.loads(cred_data)
                cred = credentials.Certificate(cred_data)
                logger.info("Firebase initialized from settings dict")

        if cred is None:
            logger.warning(
                "Firebase credentials not configured. "
                "Push notifications will be disabled."
            )
            return None

        _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app

    except ImportError:
        logger.error("firebase-admin not installed. Run: pip install firebase-admin")
        return None
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in Firebase credentials: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e)
        return None


class NotificationResult:
    """Result of a notification send operation."""

    def __init__(
        self,
        success: bool,
        message_id: str | None = None,
        error: str | None = None,
        token: str | None = None,
    ):
        self.success = success
        self.message_id = message_id
        self.error = error
        self.token = token

    def __repr__(self):
        if self.success:
            return f"NotificationResult(success=True, id={self.message_id})"
        return f"NotificationResult(success=False, error={self.error})"


class NotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging."""

    @staticmethod
    def _get_messaging():
        """Get Firebase messaging instance."""
        app = _get_firebase_app()
        if app is None:
            return None

        from firebase_admin import messaging

        return messaging

    @staticmethod
    def send(
        token: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        image_url: str | None = None,
        click_action: str | None = None,
        sound: str = "default",
        badge: int | None = None,
        priority: str = "high",
    ) -> NotificationResult:
        """
        Send a push notification to a single device.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body text
            data: Optional data payload (key-value pairs, all strings)
            image_url: Optional image URL to display
            click_action: URL or deep link to open on click
            sound: Notification sound (default: "default")
            badge: Badge number for iOS
            priority: Message priority ("high" or "normal")

        Returns:
            NotificationResult with success status and message ID or error
        """
        messaging = NotificationService._get_messaging()
        if messaging is None:
            return NotificationResult(
                success=False,
                error="Firebase not configured",
                token=token,
            )

        try:
            # Build notification payload
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url,
            )

            # Android configuration
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound=sound,
                    click_action=click_action,
                    default_sound=True if sound == "default" else False,
                    default_vibrate_timings=True,
                ),
            )

            # iOS (APNs) configuration
            apns_payload = {"aps": {"sound": sound}}
            if badge is not None:
                apns_payload["aps"]["badge"] = badge
            if click_action:
                apns_payload["aps"]["category"] = click_action

            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound=sound,
                        badge=badge,
                    )
                ),
            )

            # Web push configuration
            web_config = None
            if click_action:
                web_config = messaging.WebpushConfig(
                    fcm_options=messaging.WebpushFCMOptions(
                        link=click_action,
                    ),
                )

            # Prepare data payload (all values must be strings)
            data_payload = None
            if data:
                data_payload = {k: str(v) for k, v in data.items()}
                if click_action:
                    data_payload["click_action"] = click_action

            # Build message
            message = messaging.Message(
                notification=notification,
                android=android_config,
                apns=apns_config,
                webpush=web_config,
                data=data_payload,
                token=token,
            )

            # Send message
            message_id = messaging.send(message)

            logger.info(f"Notification sent successfully: {message_id}")
            return NotificationResult(
                success=True,
                message_id=message_id,
                token=token,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send notification: {error_msg}")

            # Check for invalid token errors
            if "not a valid FCM registration token" in error_msg.lower():
                # Mark token as invalid for cleanup
                NotificationService._handle_invalid_token(token)

            return NotificationResult(
                success=False,
                error=error_msg,
                token=token,
            )

    @staticmethod
    def _handle_invalid_token(token: str):
        """Handle invalid FCM token by clearing it from sessions."""
        try:
            from users.models.session import UserSession

            sessions = UserSession.objects.filter(fcm_token=token, is_active=True)
            for session in sessions:
                session.clear_fcm_token()
                logger.info(f"Cleared invalid FCM token from session {session.id}")
        except Exception as e:
            logger.error(f"Error clearing invalid token: {e}")

    @staticmethod
    def send_to_user(
        user_id: int,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[NotificationResult]:
        """
        Send notification to all active sessions of a user.

        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Optional data payload
            **kwargs: Additional arguments for send()

        Returns:
            List of NotificationResult for each session
        """
        from users.models.session import UserSession

        sessions = UserSession.objects.filter(
            user_id=user_id,
            is_active=True,
            fcm_token__isnull=False,
        ).exclude(fcm_token="")

        results = []
        for session in sessions:
            result = NotificationService.send(
                token=session.fcm_token,
                title=title,
                body=body,
                data=data,
                **kwargs,
            )
            results.append(result)

        return results

    @staticmethod
    def send_to_users(
        user_ids: list[int],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[int, list[NotificationResult]]:
        """
        Send notification to multiple users.

        Args:
            user_ids: List of user IDs
            title: Notification title
            body: Notification body
            data: Optional data payload
            **kwargs: Additional arguments for send()

        Returns:
            Dict mapping user_id to list of NotificationResult
        """
        results = {}
        for user_id in user_ids:
            results[user_id] = NotificationService.send_to_user(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                **kwargs,
            )
        return results

    @staticmethod
    def send_multicast(
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict:
        """
        Send notification to multiple tokens efficiently using multicast.

        Args:
            tokens: List of FCM tokens (max 500)
            title: Notification title
            body: Notification body
            data: Optional data payload

        Returns:
            Dict with success_count, failure_count, and failed_tokens
        """
        messaging = NotificationService._get_messaging()
        if messaging is None:
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "error": "Firebase not configured",
            }

        if not tokens:
            return {"success_count": 0, "failure_count": 0}

        # FCM multicast limit is 500 tokens
        if len(tokens) > 500:
            tokens = tokens[:500]
            logger.warning(
                "Multicast limited to 500 tokens. " "Consider batching for more."
            )

        try:
            notification = messaging.Notification(
                title=title,
                body=body,
            )

            data_payload = None
            if data:
                data_payload = {k: str(v) for k, v in data.items()}

            message = messaging.MulticastMessage(
                notification=notification,
                data=data_payload,
                tokens=tokens,
            )

            response = messaging.send_multicast(message)

            # Collect failed tokens for cleanup
            failed_tokens = []
            if response.failure_count > 0:
                for idx, send_response in enumerate(response.responses):
                    if not send_response.success:
                        failed_tokens.append(tokens[idx])
                        # Handle invalid tokens
                        if send_response.exception:
                            err = str(send_response.exception)
                            if "not a valid" in err.lower():
                                NotificationService._handle_invalid_token(tokens[idx])

            logger.info(
                f"Multicast sent: {response.success_count} success, "
                f"{response.failure_count} failed"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "failed_tokens": failed_tokens,
            }

        except Exception as e:
            logger.error(f"Multicast send failed: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "error": str(e),
            }

    @staticmethod
    def send_to_topic(
        topic: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """
        Send notification to a topic (all subscribed devices).

        Args:
            topic: Topic name (e.g., "promotions", "news")
            title: Notification title
            body: Notification body
            data: Optional data payload

        Returns:
            NotificationResult
        """
        messaging = NotificationService._get_messaging()
        if messaging is None:
            return NotificationResult(success=False, error="Firebase not configured")

        try:
            notification = messaging.Notification(
                title=title,
                body=body,
            )

            data_payload = None
            if data:
                data_payload = {k: str(v) for k, v in data.items()}

            message = messaging.Message(
                notification=notification,
                data=data_payload,
                topic=topic,
            )

            message_id = messaging.send(message)

            logger.info(f"Topic notification sent to '{topic}': {message_id}")
            return NotificationResult(success=True, message_id=message_id)

        except Exception as e:
            logger.error(f"Topic send failed: {e}")
            return NotificationResult(success=False, error=str(e))
