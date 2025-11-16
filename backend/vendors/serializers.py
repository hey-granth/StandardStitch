from decimal import Decimal
from typing import Any, Dict, Optional
from rest_framework import serializers
from django.utils import timezone
from django.core.cache import cache
from .models import Vendor, VendorApproval, Listing, PricePolicy


def get_price_policy_cached(school_id: str) -> Optional[Decimal]:
    """Cache price policy lookup for 5 minutes"""
    cache_key = f"price_policy:{school_id}"
    max_markup = cache.get(cache_key)
    if max_markup is None:
        try:
            policy = PricePolicy.objects.only("max_markup_pct").get(school_id=school_id)
            max_markup = policy.max_markup_pct
        except PricePolicy.DoesNotExist:
            max_markup = Decimal("30.00")
        cache.set(cache_key, max_markup, timeout=300)
    return max_markup


def get_vendor_approval_cached(
    vendor_id: str, school_id: str
) -> Optional[VendorApproval]:
    """Cache vendor approval lookup for 5 minutes"""
    cache_key = f"approval:{vendor_id}:{school_id}"
    approval_data = cache.get(cache_key)
    if approval_data is None:
        approval = (
            VendorApproval.objects.filter(
                vendor_id=vendor_id, school_id=school_id, status="approved"
            )
            .only("expires_at")
            .first()
        )
        approval_data = {
            "exists": approval is not None,
            "expires_at": approval.expires_at if approval else None,
        }
        cache.set(cache_key, approval_data, timeout=300)
    return approval_data


class VendorSerializer(serializers.ModelSerializer[Vendor]):
    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "city",
            "gstin",
            "verification_level",
            "payout_info",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "verification_level",
            "is_active",
            "created_at",
            "updated_at",
        ]


class VendorApplySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    gstin = serializers.CharField(max_length=15, required=False, allow_blank=True)
    payout_info = serializers.JSONField(default=dict)

    def create(self, validated_data: Dict[str, Any]) -> Vendor:
        return Vendor.objects.create(**validated_data)


class ListingSerializer(serializers.ModelSerializer[Listing]):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    school_name = serializers.CharField(source="school.name", read_only=True)
    spec_item_type = serializers.CharField(source="spec.item_type", read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "vendor",
            "vendor_name",
            "school",
            "school_name",
            "spec",
            "spec_item_type",
            "sku",
            "base_price",
            "mrp",
            "lead_time_days",
            "enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vendor = data.get("vendor")
        school = data.get("school")
        spec = data.get("spec")
        base_price = data.get("base_price")
        mrp = data.get("mrp")

        if not vendor.is_active:
            raise serializers.ValidationError(
                "Vendor must be active to create listings"
            )

        # Use cached approval lookup
        approval_data = get_vendor_approval_cached(str(vendor.id), str(school.id))

        if not approval_data["exists"]:
            raise serializers.ValidationError("Vendor must be approved for this school")

        if (
            approval_data["expires_at"]
            and approval_data["expires_at"] < timezone.now().date()
        ):
            raise serializers.ValidationError("Vendor approval has expired")

        if spec.school_id != school.id:
            raise serializers.ValidationError(
                "Spec must belong to the specified school"
            )

        # Use cached price policy lookup
        max_markup_pct = get_price_policy_cached(str(school.id))
        max_allowed_mrp = base_price * (Decimal("1") + max_markup_pct / Decimal("100"))
        if mrp > max_allowed_mrp:
            raise serializers.ValidationError(
                f"MRP exceeds maximum allowed markup of {max_markup_pct}%. "
                f"Max MRP: {max_allowed_mrp:.2f}"
            )

        return data


class ListingCreateSerializer(serializers.ModelSerializer[Listing]):
    class Meta:
        model = Listing
        fields = [
            "vendor",
            "school",
            "spec",
            "sku",
            "base_price",
            "mrp",
            "lead_time_days",
            "enabled",
        ]

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Reuse validation from ListingSerializer
        serializer = ListingSerializer()
        return serializer.validate(data)
