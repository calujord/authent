from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .test_error_views import test_django_500_view, TestErrorView
from .views import CountryViewSet, LocationViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r"locations", LocationViewSet)
router.register(r"countries", CountryViewSet)
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    path("test-error/", TestErrorView.as_view(), name="test-error"),
    path("test-django-error/", test_django_500_view, name="test-django-error"),
]
