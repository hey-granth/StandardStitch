from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import IntegrityError
from .models import Listing
from .serializers import (
    VendorApplySerializer,
    ListingSerializer,
    ListingCreateSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def vendor_apply(request: Request) -> Response:
    """Create a new vendor application"""
    serializer = VendorApplySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    vendor = serializer.save()

    return Response(
        {
            "id": str(vendor.id),
            "name": vendor.name,
            "is_active": vendor.is_active,
            "message": "Vendor application created. Pending approval.",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_listing(request: Request) -> Response:
    """Create a new listing with idempotency support"""
    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return Response(
            {"error": "Idempotency-Key header is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing listing with same idempotency key
    existing = Listing.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        serializer = ListingSerializer(existing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create new listing
    serializer = ListingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        listing = serializer.save(idempotency_key=idempotency_key)
        response_serializer = ListingSerializer(listing)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    except IntegrityError as e:
        return Response(
            {"error": "Duplicate listing or constraint violation"},
            status=status.HTTP_409_CONFLICT,
        )


class VendorListingViewSet(viewsets.ReadOnlyModelViewSet[Listing]):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vendor_id = self.kwargs.get("vendor_id")
        return (
            Listing.objects.filter(vendor_id=vendor_id)
            .select_related("vendor", "school", "spec")
            .order_by("-created_at")
        )
