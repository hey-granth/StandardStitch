from django.contrib import admin
from .models import Vendor, VendorApproval, PricePolicy, Listing


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "city",
        "gstin",
        "verification_level",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "verification_level", "city"]
    search_fields = ["name", "city", "gstin"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(VendorApproval)
class VendorApprovalAdmin(admin.ModelAdmin):
    list_display = ["vendor", "school", "status", "expires_at", "created_at"]
    list_filter = ["status", "expires_at"]
    search_fields = ["vendor__name", "school__name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(PricePolicy)
class PricePolicyAdmin(admin.ModelAdmin):
    list_display = ["school", "max_markup_pct", "created_at"]
    search_fields = ["school__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        "vendor",
        "school",
        "spec",
        "sku",
        "base_price",
        "mrp",
        "enabled",
        "created_at",
    ]
    list_filter = ["enabled", "school", "vendor"]
    search_fields = ["sku", "vendor__name", "school__name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "idempotency_key", "created_at", "updated_at"]
