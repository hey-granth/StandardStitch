from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import SchoolViewSet

router = DefaultRouter()
router.register(r"schools", SchoolViewSet, basename="school")

urlpatterns = [
    path("", include(router.urls)),
]

