"""
Middleware para manejar errores y devolverlos en formato JSON
"""

import logging
import traceback

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


def get_error_type(status_code):
    """
    Obtiene el tipo de error basado en el código de estado HTTP
    """
    error_types = {
        400: "bad_request",
        401: "unauthorized",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        406: "not_acceptable",
        409: "conflict",
        410: "gone",
        422: "unprocessable_entity",
        429: "throttled",
        500: "internal_server_error",
        501: "not_implemented",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout",
    }
    return error_types.get(status_code, "unknown_error")


class JsonErrorMiddleware(MiddlewareMixin):
    """
    Middleware que intercepta errores 500 y los devuelve en formato JSON
    cuando la solicitud es hacia una API o acepta JSON.
    """

    def process_exception(self, request, exception):
        """
        Procesa excepciones no manejadas y las devuelve como JSON
        si la solicitud es hacia una API.
        """
        # Verificar si es una solicitud API
        if self.is_api_request(request):
            logger.error(
                f"Error 500 en API: {type(exception).__name__}: {str(exception)}",
                exc_info=True,
            )

            # Preparar respuesta de error
            error_data = {
                "error": True,
                "message": "Error interno del servidor",
                "status_code": 500,
                "type": "internal_server_error",
            }

            # En modo DEBUG, incluir información adicional
            if settings.DEBUG:
                error_data.update(
                    {
                        "exception": type(exception).__name__,
                        "detail": str(exception),
                        "traceback": traceback.format_exc().split("\n"),
                    }
                )

            return JsonResponse(
                error_data,
                status=500,
                json_dumps_params={"ensure_ascii": False, "indent": 2},
            )

        # Si no es una solicitud API, dejar que
        # Django maneje el error normalmente
        return None

    def process_response(self, request, response):
        """
        Procesa respuestas y las convierte a JSON si es necesario
        """
        # Protección contra respuestas None
        if response is None:
            from django.http import HttpResponseServerError

            return HttpResponseServerError("Internal Server Error")

        # Verificar si es una solicitud API y si la respuesta es un error
        if (
            self.is_api_request(request)
            and response.status_code >= 400
            and hasattr(response, "content")
        ):

            # Verificar si la respuesta ya es JSON
            content_type = response.get("Content-Type", "")
            if "application/json" not in content_type:
                # Si no es JSON y es un error, convertir a JSON
                error_data = {
                    "error": True,
                    "message": self._get_error_message(response.status_code),
                    "status_code": response.status_code,
                    "type": get_error_type(response.status_code),
                }

                if settings.DEBUG:
                    error_data["original_content"] = response.content.decode(
                        "utf-8", errors="ignore"
                    )[:500]

                return JsonResponse(
                    error_data,
                    status=response.status_code,
                    json_dumps_params={"ensure_ascii": False, "indent": 2},
                )

        return response

    def _get_error_message(self, status_code):
        """
        Obtiene un mensaje de error apropiado según el código de estado
        """
        messages = {
            400: "Solicitud incorrecta",
            401: "No autorizado",
            403: "Acceso denegado",
            404: "Recurso no encontrado",
            405: "Método no permitido",
            500: "Error interno del servidor",
        }
        return messages.get(status_code, "Error en el servidor")

    def is_api_request(self, request):
        """
        Determina si la solicitud es hacia una API basándose en:
        1. El path comienza con /api/
        2. El header Accept contiene application/json
        3. El header Content-Type contiene application/json
        """
        # Verificar si la URL es de API
        if request.path.startswith("/api/"):
            return True

        # Verificar headers
        accept_header = request.META.get("HTTP_ACCEPT", "")
        content_type = request.META.get("CONTENT_TYPE", "")

        if "application/json" in accept_header:
            return True

        if "application/json" in content_type:
            return True

        return False


class Custom500Handler:
    """
    Handler personalizado para errores 500 que devuelve JSON
    """

    @staticmethod
    def handle_500_error(request):
        """
        Maneja errores 500 y los devuelve en formato JSON
        """
        logger.error("Error 500 capturado por handler personalizado")

        error_data = {
            "error": True,
            "message": "Error interno del servidor",
            "status_code": 500,
            "type": "internal_server_error",
        }

        # En modo DEBUG, incluir información adicional
        if settings.DEBUG:
            error_data["debug"] = True

        return JsonResponse(
            error_data,
            status=500,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )


def custom_500_view(request):
    """
    Vista personalizada para manejar errores 500
    """
    return Custom500Handler.handle_500_error(request)


def custom_404_view(request, exception):
    """
    Vista personalizada para manejar errores 404 en API
    """
    if request.path.startswith("/api/"):
        error_data = {
            "error": True,
            "message": "Recurso no encontrado",
            "status_code": 404,
            "type": "not_found",
        }

        if settings.DEBUG:
            error_data["path"] = request.path

        return JsonResponse(
            error_data,
            status=404,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    # Si no es API, usar respuesta HTML por defecto de Django
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)


def custom_400_view(request, exception):
    """
    Vista personalizada para manejar errores 400 en API
    """
    if request.path.startswith("/api/"):
        error_data = {
            "error": True,
            "message": "Solicitud incorrecta",
            "status_code": 400,
            "type": "bad_request",
        }

        if settings.DEBUG:
            error_data["detail"] = str(exception)

        return JsonResponse(
            error_data,
            status=400,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    from django.views.defaults import bad_request

    return bad_request(request, exception)


def custom_403_view(request, exception):
    """
    Vista personalizada para manejar errores 403 en API
    """
    if request.path.startswith("/api/"):
        error_data = {
            "error": True,
            "message": "Acceso denegado",
            "status_code": 403,
            "type": "permission_denied",
        }

        return JsonResponse(
            error_data,
            status=403,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    from django.views.defaults import permission_denied

    return permission_denied(request, exception)
