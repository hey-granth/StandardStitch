from django.contrib import admin
from .models import Cart, CartItem, Payment


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "listing", "qty", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["cart__user__email", "listing__sku"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "provider_ref", "provider", "amount", "status", "created_at"]
    list_filter = ["status", "provider", "created_at"]
    search_fields = ["provider_ref"]
    readonly_fields = ["id", "created_at", "updated_at"]
