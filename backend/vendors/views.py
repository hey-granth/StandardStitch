from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import IntegrityError, transaction
from typing import Any
from .models import Listing, Vendor
from .serializers import (
    VendorOnboardSerializer,
    VendorSerializer,
    VendorApplySerializer,
    ListingSerializer,
    ListingCreateSerializer,
)
from .permissions import IsParentRole, IsOpsOrStaff, IsApprovedVendor


@api_view(["POST"])
@permission_classes([IsParentRole])
def vendor_onboard(request: Request) -> Response:
    """
    Vendor onboarding endpoint.
    Only users with 'parent' role can onboard.
    Creates Vendor with status='pending', does NOT change user role yet.
    """
    serializer = VendorOnboardSerializer(
        data=request.data, context={"request": request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        vendor = serializer.save()
        return Response(
            VendorSerializer(vendor).data,
            status=status.HTTP_201_CREATED,
        )
    except IntegrityError as e:
        return Response(
            {"error": "Database constraint violation. GST number may already exist."},
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsOpsOrStaff])
def vendor_approve(request: Request, vendor_id: str) -> Response:
    """
    Approve vendor endpoint (admin/ops only).
    Sets vendor.status = 'approved' and vendor.user.role = 'vendor'.
    """
    try:
        vendor = Vendor.objects.select_related("user").get(id=vendor_id)
    except Vendor.DoesNotExist:
        return Response(
            {"error": "Vendor not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if vendor.status == "approved":
        return Response(
            {"message": "Vendor already approved"},
            status=status.HTTP_200_OK,
        )

    with transaction.atomic():
        vendor.status = "approved"
        vendor.is_active = True
        vendor.save(update_fields=["status", "is_active", "updated_at"])

        # Update user role to vendor
        user = vendor.user
        user.role = "vendor"
        user.save(update_fields=["role"])

    return Response(
        VendorSerializer(vendor).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsOpsOrStaff])
def vendor_reject(request: Request, vendor_id: str) -> Response:
    """
    Reject vendor endpoint (admin/ops only).
    Sets vendor.status = 'rejected'.
    """
    try:
        vendor = Vendor.objects.get(id=vendor_id)
    except Vendor.DoesNotExist:
        return Response(
            {"error": "Vendor not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    vendor.status = "rejected"
    vendor.is_active = False
    vendor.save(update_fields=["status", "is_active", "updated_at"])

    return Response(
        VendorSerializer(vendor).data,
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsOpsOrStaff])
def vendor_list(request: Request) -> Response:
    """
    List all vendors (admin/ops only).
    """
    vendors = Vendor.objects.select_related("user").order_by("-created_at")
    serializer = VendorSerializer(vendors, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_me(request: Request) -> Response:
    """
    Get current user's vendor profile.
    Returns 404 if no vendor profile exists.
    """
    if not hasattr(request.user, "vendor_profile"):
        return Response(
            {"error": "No vendor profile found for current user"},
            status=status.HTTP_404_NOT_FOUND,
        )

    vendor = request.user.vendor_profile
    return Response(
        VendorSerializer(vendor).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def vendor_apply(request: Request) -> Response:
    """Legacy vendor application endpoint (deprecated, use /vendors/onboard)"""
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
@permission_classes([IsApprovedVendor])
def create_listing(request: Request) -> Response:
    """
    Create a new listing with idempotency support.
    Only approved vendors can create listings.
    """
    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return Response(
            {"error": "Idempotency-Key header is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing listing with same idempotency key
    existing = (
        Listing.objects.filter(idempotency_key=idempotency_key)
        .select_related("vendor", "school", "spec")
        .first()
    )
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
