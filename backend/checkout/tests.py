import hashlib
from datetime import date
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from schools.models import School
from catalog.models import UniformSpec
from vendors.models import Vendor, Listing
from checkout.models import Cart, CartItem, Payment

User = get_user_model()


class CheckoutTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.user = User.objects.create_user(
            email="buyer@example.com", password="password123", role="parent"
        )

        cls.school = School.objects.create(
            name="Test School",
            code="SCH-001",
            city="Mumbai",
            address="123 Test St",
            academic_year="2025-2026",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31),
        )

        cls.spec = UniformSpec.objects.create(
            school=cls.school,
            academic_year="2025-2026",
            description="Test Description",
            item_type="shirt",
            item_name="Test Shirt",
            gender="boys",
            season="summer",
            fabric_gsm=180,
            pantone="PMS 287C",
            measurements={},
        )

        cls.vendor = Vendor.objects.create(
            name="Test Vendor", city="Mumbai", is_active=True
        )

        cls.listing = Listing.objects.create(
            vendor=cls.vendor,
            school=cls.school,
            spec=cls.spec,
            sku="SHIRT-001",
            base_price=Decimal("100.00"),
            mrp=Decimal("120.00"),
            lead_time_days=7,
            enabled=True,
        )

    def setUp(self):
        """Per-test setup - only authenticate, clear cache"""
        self.client.force_authenticate(user=self.user)
        from django.core.cache import cache
        cache.clear()

    def test_add_cart_item(self):
        """Test adding item to cart"""
        url = reverse("cart-add-item")
        data = {"listing": str(self.listing.id), "qty": 2}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["qty"], 2)
        self.assertEqual(response.data["listing_sku"], "SHIRT-001")

        # Verify cart item created
        cart_item = CartItem.objects.filter(listing=self.listing).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.qty, 2)

    def test_update_cart_item(self):
        """Test updating existing cart item"""
        # Create initial cart item
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, listing=self.listing, qty=1)

        url = reverse("cart-add-item")
        data = {"listing": str(self.listing.id), "qty": 5}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["qty"], 5)

        # Verify only one cart item exists
        self.assertEqual(CartItem.objects.filter(listing=self.listing).count(), 1)

    def test_remove_cart_item(self):
        """Test removing item from cart"""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, listing=self.listing, qty=2)

        url = reverse("cart-remove-item", kwargs={"item_id": cart_item.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())

    def test_get_cart(self):
        """Test getting cart with items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, listing=self.listing, qty=3)

        url = reverse("cart-get")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["qty"], 3)

        # Verify total amount calculation
        expected_total = Decimal("120.00") * 3
        self.assertEqual(Decimal(response.data["total_amount"]), expected_total)

    def test_checkout_session_creates_payment(self):
        """Test creating checkout session"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, listing=self.listing, qty=2)

        url = reverse("checkout-session")
        data = {"cart_id": str(cart.id)}

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-checkout-123"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("payment_token", response.data)
        self.assertIn("payment_id", response.data)
        self.assertEqual(response.data["status"], "pending")

        # Verify payment created
        payment = Payment.objects.get(id=response.data["payment_id"])
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.amount, Decimal("240.00"))  # 120 * 2

    def test_checkout_session_idempotency(self):
        """Test checkout session idempotency"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, listing=self.listing, qty=1)

        url = reverse("checkout-session")
        data = {"cart_id": str(cart.id)}
        idempotency_key = "test-idem-456"

        # First request
        response1 = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY=idempotency_key
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second request with same key
        response2 = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY=idempotency_key
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["payment_id"], response2.data["payment_id"])

    def test_checkout_session_empty_cart(self):
        """Test checkout with empty cart fails"""
        cart = Cart.objects.create(user=self.user)

        url = reverse("checkout-session")
        data = {"cart_id": str(cart.id)}

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-empty-cart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("empty", str(response.data).lower())

    def test_webhook_updates_payment_status(self):
        """Test webhook updates payment status"""
        payment = Payment.objects.create(
            provider="mock_psp",
            provider_ref="mock_pi_test123",
            amount=Decimal("100.00"),
            status="pending",
        )

        # Generate valid signature
        signature = hashlib.sha256(
            f"{payment.provider_ref}:mock_secret".encode()
        ).hexdigest()

        url = reverse("payment-webhook")
        data = {
            "provider_ref": payment.provider_ref,
            "status": "paid",
            "signature": signature,
            "raw_data": {"transaction_id": "txn_123"},
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["new_status"], "paid")

        # Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, "paid")
        self.assertIn("transaction_id", payment.raw_payload)

    def test_webhook_invalid_signature(self):
        """Test webhook rejects invalid signature"""
        payment = Payment.objects.create(
            provider="mock_psp",
            provider_ref="mock_pi_test456",
            amount=Decimal("100.00"),
            status="pending",
        )

        url = reverse("payment-webhook")
        data = {
            "provider_ref": payment.provider_ref,
            "status": "paid",
            "signature": "invalid_signature",
            "raw_data": {},
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify payment not updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")

    def test_webhook_idempotency(self):
        """Test webhook prevents duplicate processing"""
        payment = Payment.objects.create(
            provider="mock_psp",
            provider_ref="mock_pi_test789",
            amount=Decimal("100.00"),
            status="pending",
        )

        signature = hashlib.sha256(
            f"{payment.provider_ref}:mock_secret".encode()
        ).hexdigest()

        url = reverse("payment-webhook")
        data = {
            "provider_ref": payment.provider_ref,
            "status": "paid",
            "signature": signature,
            "raw_data": {},
        }

        # First webhook
        response1 = self.client.post(url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second webhook (duplicate)
        response2 = self.client.post(url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["status"], "already_processed")
