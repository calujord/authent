"""
Vista de prueba para generar errores y probar el manejo de errores JSON
"""

from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class TestErrorView(APIView):
    """
    Vista para probar el manejo de errores
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Genera diferentes tipos de errores para prueba
        """
        error_type = request.query_params.get("type", "500")

        if error_type == "500":
            # Error 500 - División por cero
            result = 1 / 0
            return Response({"result": result})

        elif error_type == "404":
            # Error 404 - Objeto no encontrado
            from django.http import Http404

            raise Http404("Recurso no encontrado")

        elif error_type == "400":
            # Error 400 - Solicitud incorrecta
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Datos de entrada inválidos")

        elif error_type == "403":
            # Error 403 - Acceso denegado
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("No tienes permisos para esta acción")

        elif error_type == "key_error":
            # Error 500 - KeyError
            data = {}
            return Response({"value": data["nonexistent_key"]})

        elif error_type == "attribute_error":
            # Error 500 - AttributeError
            obj = None
            return Response({"value": obj.some_attribute})

        else:
            return Response(
                {
                    "message": "Especifica un tipo de error: 500, 404, 400, 403, key_error, attribute_error",
                    "example": "/api/test-error/?type=500",
                }
            )


def test_django_500_view(request):
    """
    Vista Django normal que genera un error 500
    """
    # Error fuera del contexto de DRF
    result = 1 / 0
    return JsonResponse({"result": result})
