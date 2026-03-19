from rest_framework.throttling import AnonRateThrottle


class RegisterRateThrottle(AnonRateThrottle):
    """Rate throttle for user registration: 10 attempts per hour per IP."""

    rate = "10/hour"
    scope = "register"


class CheckEmailRateThrottle(AnonRateThrottle):
    """Rate throttle for check-email step: 5 attempts per hour per IP."""

    rate = "5/hour"
    scope = "check_email"


class VerificationRateThrottle(AnonRateThrottle):
    """Rate throttle for email verification: 20 attempts per hour per IP."""

    rate = "20/hour"
    scope = "verify_email"


class ResendVerificationRateThrottle(AnonRateThrottle):
    """Rate throttle for resend verification: 3 attempts per hour per IP."""

    rate = "3/hour"
    scope = "resend_verification"
