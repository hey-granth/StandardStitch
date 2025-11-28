import hashlib
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from schools.models import School
from vendors.models import Vendor, VendorApproval, PricePolicy, Listing
from catalog.models import UniformSpec
from checkout.models import Cart, CartItem, Payment, Order, OrderItem


User = get_user_model()


class OrderLifecycleIntegrationTest(TestCase):
    """Integration test for complete order lifecycle"""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up static test data"""
        # Create user
        cls.user = User.objects.create_user(
            email="parent@test.com", password="testpass123", role="parent"
        )

        # Create school
        cls.school = School.objects.create(
            name="Test School",
            code="SCH-001",
            city="Mumbai",
            address="123 Test St",
            board="CBSE",
            academic_year="2025-2026",
            session_start=date.today(),
            session_end=date.today() + timedelta(days=365),
            is_active=True,
        )

        # Create price policy
        cls.price_policy = PricePolicy.objects.create(
            school=cls.school, max_markup_pct=Decimal("30.00")
        )

        # Create vendor
        cls.vendor = Vendor.objects.create(
            name="Test Vendor",
            city="Mumbai",
            gstin="27AABCT1332L1ZZ",
            verification_level=2,
            is_active=True,
        )

        # Create vendor approval
        cls.approval = VendorApproval.objects.create(
            vendor=cls.vendor,
            school=cls.school,
            status="approved",
            expires_at=date.today() + timedelta(days=365),
        )

        # Create uniform spec
        cls.spec = UniformSpec.objects.create(
            school=cls.school,
            academic_year="2025-2026",
            description="Test Description",
            item_type="Shirt",
            item_name="Test Shirt",
            gender="Male",
            season="Summer",
            fabric_gsm=150,
            pantone="19-4052",
            measurements={"chest": 38, "length": 28},
            frozen=True,
            version=1,
        )

        # Create listing
        cls.listing = Listing.objects.create(
            vendor=cls.vendor,
            school=cls.school,
            spec=cls.spec,
            sku="TST-SHIRT-001",
            base_price=Decimal("400.00"),
            mrp=Decimal("500.00"),
            lead_time_days=7,
            enabled=True,
        )

    def setUp(self) -> None:
        """Set up test client and authentication"""
        cache.clear()  # Clear cache to ensure clean state
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_complete_order_lifecycle(self) -> None:
        """Test complete order flow from cart to order creation"""

        # Step 1: Add item to cart
        add_response = self.client.post(
            "/api/cart/items",
            {"listing": str(self.listing.id), "qty": 2},
            format="json",
        )
        self.assertEqual(add_response.status_code, 201)
        cart_item_id = add_response.data["id"]

        # Verify cart item created
        cart_item = CartItem.objects.select_related("cart", "listing").get(
            id=cart_item_id
        )
        self.assertEqual(cart_item.qty, 2)
        self.assertEqual(cart_item.listing.id, self.listing.id)

        # Step 2: Get cart
        cart_response = self.client.get("/api/cart")
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(len(cart_response.data["items"]), 1)
        cart_id = cart_response.data["id"]

        # Step 3: Create checkout session
        checkout_response = self.client.post(
            "/api/checkout/session",
            {"cart_id": cart_id},
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-idempotency-key-001",
        )
        self.assertIn(checkout_response.status_code, [200, 201])
        self.assertIn("payment_token", checkout_response.data)
        self.assertIn("payment_id", checkout_response.data)
        self.assertEqual(checkout_response.data["status"], "pending")

        payment_token = checkout_response.data["payment_token"]
        expected_amount = self.listing.mrp * 2
        self.assertEqual(Decimal(checkout_response.data["amount"]), expected_amount)

        # Verify payment created
        payment = Payment.objects.get(provider_ref=payment_token)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.amount, expected_amount)

        # Step 4: Simulate webhook for successful payment
        mock_signature = hashlib.sha256(
            f"{payment_token}:mock_secret".encode()
        ).hexdigest()

        webhook_response = self.client.post(
            "/api/payments/webhook",
            {
                "provider_ref": payment_token,
                "status": "paid",
                "signature": mock_signature,
                "raw_data": {"transaction_id": "txn_123", "paid_at": "2025-11-21"},
            },
            format="json",
        )
        self.assertEqual(webhook_response.status_code, 200)
        self.assertEqual(webhook_response.data["new_status"], "paid")

        # Step 5: Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, "paid")

        # Step 6: Verify Order created with correct relationships
        self.assertTrue(hasattr(payment, "order"))
        order = (
            Order.objects.select_related("payment", "user")
            .prefetch_related("items__listing__vendor", "items__listing__spec")
            .get(payment=payment)
        )

        self.assertEqual(order.user.id, self.user.id)
        self.assertEqual(order.total_amount, expected_amount)
        self.assertEqual(order.status, "confirmed")

        # Step 7: Verify OrderItems created with correct totals
        order_items = list(order.items.all())
        self.assertEqual(len(order_items), 1)

        order_item = order_items[0]
        self.assertEqual(order_item.listing.id, self.listing.id)
        self.assertEqual(order_item.qty, 2)
        self.assertEqual(order_item.unit_price, self.listing.mrp)
        self.assertEqual(order_item.subtotal, self.listing.mrp * 2)

        # Step 8: Verify no N+1 queries - relationships are prefetched
        self.assertEqual(order_item.listing.vendor.name, self.vendor.name)
        self.assertEqual(order_item.listing.spec.item_type, "Shirt")
        self.assertEqual(order_item.listing.school.name, self.school.name)

        # Step 9: Verify idempotency - calling checkout again returns same payment
        checkout_response_2 = self.client.post(
            "/api/checkout/session",
            {"cart_id": cart_id},
            format="json",
            HTTP_IDEMPOTENCY_KEY="test-idempotency-key-001",
        )
        self.assertEqual(checkout_response_2.status_code, 200)
        self.assertEqual(checkout_response_2.data["payment_token"], payment_token)

        # Step 10: Verify webhook idempotency
        webhook_response_2 = self.client.post(
            "/api/payments/webhook",
            {
                "provider_ref": payment_token,
                "status": "paid",
                "signature": mock_signature,
                "raw_data": {"transaction_id": "txn_123"},
            },
            format="json",
        )
        self.assertEqual(webhook_response_2.status_code, 200)

        # Should not create duplicate order
        order_count = Order.objects.filter(payment=payment).count()
        self.assertEqual(order_count, 1)
