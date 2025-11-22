import hashlib
import secrets
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from vendors.models import Listing
from .models import Cart, CartItem, Payment, Order, OrderItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CheckoutSessionSerializer,
    WebhookPayloadSerializer,
)


def get_or_create_cart(user) -> Cart:
    """Get user's active cart or create new one (optimized)"""
    cart = Cart.objects.filter(user=user).only("id", "user_id", "updated_at").order_by("-updated_at").first()
    if not cart:
        cart = Cart.objects.create(user=user)
    return cart


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_cart_item(request: Request) -> Response:
    """Add or update cart item"""
    serializer = CartItemCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    listing_id = serializer.validated_data["listing"]
    qty = serializer.validated_data["qty"]

    # Verify listing exists and is enabled (minimal fields)
    listing = get_object_or_404(
        Listing.objects.only("id", "enabled"),
        id=listing_id,
        enabled=True,
    )

    cart = get_or_create_cart(request.user)

    # Update or create cart item
    cart_item, created = CartItem.objects.update_or_create(
        cart=cart, listing_id=listing_id, defaults={"qty": qty}
    )

    # Reload with relations for serializer
    cart_item = CartItem.objects.select_related(
        "listing__vendor", "listing__school"
    ).get(id=cart_item.id)

    response_serializer = CartItemSerializer(cart_item)
    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_cart_item(request: Request, item_id: str) -> Response:
    """Remove item from cart"""
    cart = get_or_create_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request: Request) -> Response:
    """Get user's cart with items"""
    cart = get_or_create_cart(request.user)

    # Prefetch items with related data
    cart = Cart.objects.prefetch_related(
        "items__listing__vendor", "items__listing__school", "items__listing__spec"
    ).get(id=cart.id)

    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_checkout_session(request: Request) -> Response:
    """Create payment session with idempotency"""
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return Response(
            {"error": "Idempotency-Key header is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing payment with same idempotency key
    cache_key = f"checkout_session:{idempotency_key}"
    cached_payment = cache.get(cache_key)
    if cached_payment:
        return Response(cached_payment, status=status.HTTP_200_OK)

    serializer = CheckoutSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cart_id = serializer.validated_data["cart_id"]
    cart = get_object_or_404(
        Cart.objects.prefetch_related("items__listing"), id=cart_id, user=request.user
    )

    if not cart.items.exists():
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate total
    total_amount = Decimal("0")
    for item in cart.items.all():
        total_amount += item.listing.mrp * item.qty

    # Create mock payment intent
    provider_ref = f"mock_pi_{secrets.token_urlsafe(16)}"
    payment = Payment.objects.create(
        provider="mock_psp",
        provider_ref=provider_ref,
        amount=total_amount,
        status="pending",
        raw_payload={
            "cart_id": str(cart.id),
            "idempotency_key": idempotency_key,
            "items_count": cart.items.count(),
        },
    )

    response_data = {
        "payment_id": str(payment.id),
        "payment_token": provider_ref,
        "amount": str(payment.amount),
        "status": payment.status,
    }

    # Cache for idempotency
    cache.set(cache_key, response_data, timeout=300)

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def payment_webhook(request: Request) -> Response:
    """Handle payment provider webhook"""
    serializer = WebhookPayloadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    provider_ref = serializer.validated_data["provider_ref"]
    new_status = serializer.validated_data["status"]
    signature = serializer.validated_data["signature"]
    raw_data = serializer.validated_data["raw_data"]

    # Verify signature (mock verification)
    expected_signature = hashlib.sha256(
        f"{provider_ref}:mock_secret".encode()
    ).hexdigest()

    if signature != expected_signature:
        return Response(
            {"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # Check cache for recent webhook
    cache_key = f"webhook:{provider_ref}:{new_status}"
    if cache.get(cache_key):
        return Response({"status": "already_processed"}, status=status.HTTP_200_OK)

    # Update payment
    payment = get_object_or_404(Payment, provider_ref=provider_ref)
    payment.status = new_status
    payment.raw_payload.update(raw_data)
    payment.save(update_fields=["status", "raw_payload", "updated_at"])

    # Cache webhook to prevent duplicates
    cache.set(cache_key, True, timeout=600)

    # Create order if paid
    if new_status == "paid":
        cart_id = payment.raw_payload.get("cart_id")
        if cart_id and not hasattr(payment, "order"):
            cart = Cart.objects.prefetch_related(
                "items__listing__vendor", "items__listing__school"
            ).get(id=cart_id)

            # Create order
            order = Order.objects.create(
                user=cart.user, payment=payment, total_amount=payment.amount, status="confirmed"
            )

            # Create order items in bulk for performance
            order_items = [
                OrderItem(
                    order=order,
                    listing=cart_item.listing,
                    qty=cart_item.qty,
                    unit_price=cart_item.listing.mrp,
                    subtotal=cart_item.listing.mrp * cart_item.qty,
                )
                for cart_item in cart.items.all()
            ]
            OrderItem.objects.bulk_create(order_items)

    return Response(
        {
            "status": "processed",
            "payment_id": str(payment.id),
            "new_status": payment.status,
        },
        status=status.HTTP_200_OK,
    )
