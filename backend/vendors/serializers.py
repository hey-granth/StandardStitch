from decimal import Decimal
from typing import Any, Dict, Optional
import re
from rest_framework import serializers
from django.utils import timezone
from django.core.cache import cache
from .models import Vendor, VendorApproval, Listing, PricePolicy


def validate_gst_number(gst: str) -> str:
    """Validate GST number format (15 characters, alphanumeric)"""
    if not gst:
        raise serializers.ValidationError("GST number is required")

    # GST format: 2 digits (state code) + 10 chars (PAN) + 1 char (entity) + 1 char (Z) + 1 check digit
    gst_pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

    if not re.match(gst_pattern, gst.upper()):
        raise serializers.ValidationError(
            "Invalid GST number format. Must be 15 alphanumeric characters."
        )

    return gst.upper()


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
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "user",
            "user_email",
            "user_role",
            "gst_number",
            "official_name",
            "email",
            "phone",
            "city",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]


class VendorOnboardSerializer(serializers.Serializer):
    gst_number = serializers.CharField(max_length=15)
    official_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    city = serializers.CharField(max_length=100)

    def validate_gst_number(self, value: str) -> str:
        """Validate GST format and uniqueness"""
        if not value:
            raise serializers.ValidationError("GST number is required")

        validated_gst = validate_gst_number(value)

        if Vendor.objects.filter(gst_number=validated_gst).exists():
            raise serializers.ValidationError("GST number already registered")

        return validated_gst

    def create(self, validated_data: Dict[str, Any]) -> Vendor:
        user = self.context["request"].user

        # Check if user already has a vendor profile
        if hasattr(user, "vendor_profile") and user.vendor_profile is not None:
            raise serializers.ValidationError("User already has a vendor profile")

        vendor = Vendor.objects.create(
            user=user,
            gst_number=validated_data["gst_number"],
            official_name=validated_data["official_name"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            city=validated_data["city"],
            status="pending",
            is_active=False,
        )
        return vendor


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

        # Only fetch vendor status if vendor is not already loaded with these fields
        if vendor and (not hasattr(vendor, 'status') or not hasattr(vendor, 'is_active')):
            # Reload vendor with minimal fields
            from .models import Vendor
            vendor_data = Vendor.objects.only("status", "is_active").get(id=vendor.id if hasattr(vendor, 'id') else vendor)
            vendor_status = vendor_data.status
            vendor_active = vendor_data.is_active
        else:
            vendor_status = vendor.status
            vendor_active = vendor.is_active

        if vendor_status != "approved":
            raise serializers.ValidationError(
                "Only approved vendors can create listings"
            )

        if not vendor_active:
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
