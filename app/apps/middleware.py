from django.http import JsonResponse
from django.utils import timezone


# Rutas que no requieren API key
_EXEMPT_PREFIXES = (
    "/admin/",
    "/api/schema/",
    "/api/docs/",
    "/api/redoc/",
    "/health/",
    "/ready/",
    "/live/",
)


class APIKeyMiddleware:
    """
    Middleware que valida la API key en todas las requests a /api/.

    El cliente debe enviar el header:
        X-API-Key: <api_key>

    Si la key no existe, está inactiva o ha expirado, devuelve 401.
    Al validar correctamente adjunta `request.api_key` y `request.application`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._requires_api_key(request.path):
            error = self._validate(request)
            if error:
                return error

        return self.get_response(request)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _requires_api_key(self, path: str) -> bool:
        if not path.startswith("/api/"):
            return False
        return not any(path.startswith(exempt) for exempt in _EXEMPT_PREFIXES)

    def _validate(self, request):
        from apps.models import APIKey

        raw_key = request.META.get("HTTP_X_API_KEY", "").strip()

        if not raw_key:
            return JsonResponse(
                {"error": "API key required.", "code": "missing_api_key"},
                status=401,
            )

        try:
            api_key = APIKey.objects.select_related("application").get(
                key=raw_key,
                is_active=True,
                application__is_active=True,
            )
        except APIKey.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid or inactive API key.", "code": "invalid_api_key"},
                status=401,
            )

        if api_key.expires_at and api_key.expires_at < timezone.now():
            return JsonResponse(
                {"error": "API key has expired.", "code": "expired_api_key"},
                status=401,
            )

        # Actualizar last_used_at sin cargar el objeto completo
        api_key.mark_used()

        # Adjuntar al request para uso en vistas
        request.api_key = api_key
        request.application = api_key.application

        return None
