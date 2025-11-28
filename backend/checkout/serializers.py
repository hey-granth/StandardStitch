from decimal import Decimal
from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem, Payment


class CartItemSerializer(serializers.ModelSerializer[CartItem]):
    listing_sku = serializers.CharField(source="listing.sku", read_only=True)
    spec_name = serializers.CharField(source="listing.spec.item_type", read_only=True)
    vendor_name = serializers.CharField(source="listing.vendor.official_name", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "listing",
            "listing_sku",
            "spec_name",
            "vendor_name",
            "qty",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "listing_sku", "spec_name", "vendor_name", "created_at", "updated_at"]

    def validate_qty(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartItemCreateSerializer(serializers.Serializer):
    listing = serializers.UUIDField()
    qty = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer[Cart]):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_amount", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "items", "total_amount", "created_at", "updated_at"]

    def get_total_amount(self, obj: Cart) -> Decimal:
        total = Decimal("0")
        for item in obj.items.select_related("listing").all():
            total += item.listing.mrp * item.qty
        return total


class CheckoutSessionSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()


class OrderItemSerializer(serializers.ModelSerializer[OrderItem]):
    spec_name = serializers.CharField(source="listing.spec.item_type", read_only=True)
    vendor_name = serializers.CharField(source="listing.vendor.official_name", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "listing",
            "spec_name",
            "vendor_name",
            "qty",
            "unit_price",
            "subtotal",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(serializers.ModelSerializer[Order]):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "payment",
            "total_amount",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "payment", "total_amount", "created_at", "updated_at"]


class WebhookPayloadSerializer(serializers.Serializer):
    provider_ref = serializers.CharField()
    status = serializers.ChoiceField(choices=Payment.STATUS_CHOICES)
    signature = serializers.CharField()
    raw_data = serializers.JSONField(default=dict, required=False)

    def validate_status(self, value: str) -> str:
        allowed = {choice[0] for choice in Payment.STATUS_CHOICES}
        if value not in allowed:
            raise serializers.ValidationError("Invalid payment status")
        return value
