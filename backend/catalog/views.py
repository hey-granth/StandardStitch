from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from typing import Any
from schools.models import School
from .models import UniformSpec
from .serializers import UniformSpecSerializer


class CatalogViewSet(viewsets.ReadOnlyModelViewSet[UniformSpec]):
    serializer_class = UniformSpecSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["item_type", "gender"]
    ordering_fields = ["item_type", "gender", "version"]
    ordering = ["item_type"]

    def get_queryset(self):
        school_id = self.kwargs.get("school_id")
        # select_related already applied - school is always needed for serializer
        return UniformSpec.objects.filter(school_id=school_id).select_related("school").only(
            "id", "school_id", "item_type", "gender", "season",
            "fabric_gsm", "pantone", "measurements", "frozen",
            "version", "created_at", "updated_at",
            "school__name"  # Only load school name for serializer
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        school_id = kwargs.get("school_id")

        # Check if school exists
        get_object_or_404(School, id=school_id)

        # Build cache key based on query params
        query_params = request.query_params.urlencode()
        cache_key = (
            f"catalog:{school_id}:{query_params}"
            if query_params
            else f"catalog:{school_id}"
        )

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Get from database
        response = super().list(request, *args, **kwargs)

        # Cache the response
        cache.set(cache_key, response.data, timeout=60 * 5)

        return response
