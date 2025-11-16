from decimal import Decimal
from rest_framework import serializers
from .models import Cart, CartItem, Payment


class CartItemSerializer(serializers.ModelSerializer[CartItem]):
    listing_sku = serializers.CharField(source="listing.sku", read_only=True)
    listing_price = serializers.DecimalField(
        source="listing.mrp", max_digits=10, decimal_places=2, read_only=True
    )
    vendor_name = serializers.CharField(source="listing.vendor.name", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "listing",
            "listing_sku",
            "listing_price",
            "vendor_name",
            "qty",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CartItemCreateSerializer(serializers.Serializer):
    listing = serializers.UUIDField()
    qty = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer[Cart]):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_amount", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_total_amount(self, obj: Cart) -> Decimal:
        total = Decimal("0")
        for item in obj.items.all():
            total += item.listing.mrp * item.qty
        return total


class CheckoutSessionSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()


class PaymentSerializer(serializers.ModelSerializer[Payment]):
    class Meta:
        model = Payment
        fields = [
            "id",
            "provider",
            "provider_ref",
            "amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WebhookPayloadSerializer(serializers.Serializer):
    provider_ref = serializers.CharField()
    status = serializers.ChoiceField(choices=["pending", "paid", "failed"])
    signature = serializers.CharField()
    raw_data = serializers.JSONField()
