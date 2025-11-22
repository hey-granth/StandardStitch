from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from typing import Any
from .models import School
from .serializers import SchoolSerializer


class SchoolViewSet(viewsets.ReadOnlyModelViewSet[School]):
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["city"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        # Only load fields needed by serializer
        return School.objects.only(
            "id", "name", "city", "board",
            "session_start", "session_end",
            "is_active", "created_at", "updated_at"
        )

    @method_decorator(cache_page(60 * 5))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        school_id = kwargs.get("pk")
        cache_key = f"school_{school_id}"

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Get from database
        response = super().retrieve(request, *args, **kwargs)

        # Cache the response
        cache.set(cache_key, response.data, timeout=60 * 5)

        return response
