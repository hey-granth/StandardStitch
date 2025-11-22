import uuid
from decimal import Decimal
from typing import ClassVar
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Vendor(models.Model):
    STATUS_CHOICES: list[tuple[str, str]] = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendor_profile",
        null=True,
        blank=True,
    )
    gst_number = models.CharField(
        max_length=15, unique=True, db_index=True, null=True, blank=True
    )
    official_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=15, blank=True, default="")
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Legacy fields (keep for backward compatibility)
    name = models.CharField(max_length=255, blank=True, default="")
    gstin = models.CharField(max_length=15, null=True, blank=True)
    verification_level = models.IntegerField(default=0)
    payout_info = models.JSONField(default=dict)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vendors"
        indexes = [
            models.Index(fields=["city", "is_active"], name="idx_vendor_city_active"),
            models.Index(fields=["status"], name="idx_vendor_status"),
            models.Index(fields=["gst_number"], name="idx_vendor_gst"),
        ]

    def __str__(self) -> str:
        return self.official_name or self.name


class VendorApproval(models.Model):
    objects: ClassVar[models.Manager]

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        "Vendor", on_delete=models.CASCADE, related_name="approvals"
    )
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="vendor_approvals"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    expires_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vendor_approvals"
        unique_together = [["vendor", "school"]]
        indexes = [
            models.Index(fields=["vendor", "school"], name="idx_vendor_school"),
        ]

    def __str__(self) -> str:
        return f"{self.vendor.name} - {self.school.name} ({self.status})"


class PricePolicy(models.Model):
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.OneToOneField(
        "schools.School", on_delete=models.CASCADE, related_name="price_policy"
    )
    max_markup_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("30.00")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "price_policies"

    def __str__(self) -> str:
        return f"{self.school.name} - Max Markup: {self.max_markup_pct}%"


class Listing(models.Model):
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        "Vendor", on_delete=models.PROTECT, related_name="listings"
    )
    school = models.ForeignKey(
        "schools.School", on_delete=models.PROTECT, related_name="listings"
    )
    spec = models.ForeignKey(
        "catalog.UniformSpec", on_delete=models.PROTECT, related_name="listings"
    )
    sku = models.CharField(max_length=100)
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    mrp = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    lead_time_days = models.IntegerField(validators=[MinValueValidator(1)])
    enabled = models.BooleanField(default=True)
    idempotency_key = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "listings"
        indexes = [
            models.Index(
                fields=["school", "spec", "enabled"], name="idx_listing_sch_spec_en"
            ),
            models.Index(fields=["vendor", "enabled"], name="idx_listing_vendor_en"),
            models.Index(fields=["enabled", "created_at"], name="idx_listing_en_created"),
            models.Index(fields=["vendor", "school"], name="idx_listing_vendor_school"),
        ]
        constraints = []

    def __str__(self) -> str:
        return f"{self.vendor.name} - {self.spec.item_type} ({self.sku})"
