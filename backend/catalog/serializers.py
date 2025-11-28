from rest_framework import serializers
from .models import UniformSpec


class UniformSpecSerializer(serializers.ModelSerializer[UniformSpec]):
    school_name = serializers.CharField(source="school.name", read_only=True)
    listings = serializers.SerializerMethodField()

    def get_listings(self, obj):
        # Return active listings for this spec
        listings = obj.listings.filter(enabled=True, vendor__status="approved", vendor__is_active=True)
        return [
            {
                "id": str(l.id),
                "vendor_name": l.vendor.official_name,
                "price": str(l.base_price),
                "mrp": str(l.mrp),
                "sku": l.sku,
                "lead_time_days": l.lead_time_days,
            }
            for l in listings
        ]

    class Meta:
        model = UniformSpec
        fields = [
            "id",
            "school",
            "school_name",
            "academic_year",
            "description",
            "item_type",
            "item_name",
            "gender",
            "season",
            "fabric_gsm",
            "pantone",
            "measurements",
            "frozen",
            "version",
            "listings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
