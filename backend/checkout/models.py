import uuid
from decimal import Decimal
from typing import ClassVar
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Cart(models.Model):
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"], name="idx_cart_user_updated"),
        ]

    def __str__(self) -> str:
        return f"Cart {self.id} - {self.user.email}"


class CartItem(models.Model):
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey("Cart", on_delete=models.CASCADE, related_name="items")
    listing = models.ForeignKey(
        "vendors.Listing", on_delete=models.PROTECT, related_name="cart_items"
    )
    qty = models.IntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_items"
        unique_together = [["cart", "listing"]]
        indexes = [
            models.Index(fields=["cart", "listing"], name="idx_cart_listing"),
        ]

    def __str__(self) -> str:
        return f"CartItem {self.listing.sku} x{self.qty}"


class Payment(models.Model):
    objects: ClassVar[models.Manager]

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50)
    provider_ref = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["provider_ref"], name="idx_payment_provider_ref"),
            models.Index(
                fields=["status", "created_at"], name="idx_payment_status_created"
            ),
        ]

    def __str__(self) -> str:
        return f"Payment {self.provider_ref} - {self.status}"


class Order(models.Model):
    objects: ClassVar[models.Manager]

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    payment = models.OneToOneField(
        "Payment", on_delete=models.PROTECT, related_name="order", null=True
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_order_user_status"),
        ]

    def __str__(self) -> str:
        return f"Order {self.id} - {self.user.email}"


class OrderItem(models.Model):
    objects: ClassVar[models.Manager]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="items")
    listing = models.ForeignKey(
        "vendors.Listing", on_delete=models.PROTECT, related_name="order_items"
    )
    qty = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order", "listing"], name="idx_order_item"),
        ]

    def __str__(self) -> str:
        return f"OrderItem {self.listing.sku} x{self.qty}"
