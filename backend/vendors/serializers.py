from decimal import Decimal
from typing import Any, Dict
from rest_framework import serializers
from django.utils import timezone
from .models import Vendor, VendorApproval, Listing, PricePolicy


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

        # Check vendor is active
        if not vendor.is_active:
            raise serializers.ValidationError(
                "Vendor must be active to create listings"
            )

        # Check vendor has approval for school
        approval = VendorApproval.objects.filter(
            vendor=vendor, school=school, status="approved"
        ).first()

        if not approval:
            raise serializers.ValidationError("Vendor must be approved for this school")

        # Check approval expiry
        if approval.expires_at and approval.expires_at < timezone.now().date():
            raise serializers.ValidationError("Vendor approval has expired")

        # Check spec exists and belongs to school
        if spec.school_id != school.id:
            raise serializers.ValidationError(
                "Spec must belong to the specified school"
            )

        # Validate price cap
        try:
            price_policy = PricePolicy.objects.get(school=school)
        except PricePolicy.DoesNotExist:
            # Default policy if none exists
            max_markup_pct = Decimal("30.00")
        else:
            max_markup_pct = price_policy.max_markup_pct

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
