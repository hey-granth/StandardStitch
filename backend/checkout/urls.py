from django.urls import path
from . import views

urlpatterns = [
    path("cart/items", views.add_cart_item, name="cart-add-item"),
    path("cart/items/<uuid:item_id>", views.remove_cart_item, name="cart-remove-item"),
    path("cart", views.get_cart, name="cart-get"),
    path("checkout/session", views.create_checkout_session, name="checkout-session"),
    path("orders", views.list_orders, name="orders-list"),
    path("payments/webhook", views.payment_webhook, name="payment-webhook"),
]
