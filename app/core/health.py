import time

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


@csrf_exempt
@require_GET
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        - 200: System is healthy
        - 503: System has issues
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "environment": getattr(settings, "ENVIRONMENT", "unknown"),
        "checks": {},
    }

    try:
        # Database connectivity check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}

    try:
        # Redis connectivity check (if available)
        import redis

        redis_client = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            decode_responses=True,
        )
        redis_start = time.time()
        redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time": round((time.time() - redis_start) * 1000, 2),
        }
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Overall response time
    health_status["response_time"] = round((time.time() - start_time) * 1000, 2)

    # Determine HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)


@csrf_exempt
@require_GET
def ready_check(request):
    """
    Readiness check for Kubernetes.

    Returns 200 when the application is ready to serve traffic.
    """
    return JsonResponse({"status": "ready", "timestamp": int(time.time())})


@csrf_exempt
@require_GET
def live_check(request):
    """
    Liveness check for Kubernetes.

    Returns 200 when the application is alive.
    """
    return JsonResponse({"status": "alive", "timestamp": int(time.time())})
