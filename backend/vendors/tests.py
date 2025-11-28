from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from schools.models import School
from catalog.models import UniformSpec
from vendors.models import Vendor, VendorApproval, PricePolicy, Listing

User = get_user_model()


class VendorTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.user = User.objects.create_user(
            email="test@example.com", password="password123", role="vendor"
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
            name="Test Vendor",
            city="Mumbai",
            is_active=True,
            status="approved",
            user=cls.user,
        )

        cls.approval = VendorApproval.objects.create(
            vendor=cls.vendor,
            school=cls.school,
            status="approved",
            expires_at=date.today() + timedelta(days=365),
        )

        cls.price_policy = PricePolicy.objects.create(
            school=cls.school, max_markup_pct=Decimal("30.00")
        )

    def setUp(self):
        """Per-test setup - only authenticate and clear cache"""
        from django.core.cache import cache
        cache.clear()
        self.client.force_authenticate(user=self.user)

    def test_vendor_apply(self):
        """Test vendor application"""
        url = reverse("vendor-apply")
        data = {
            "name": "Test Vendor",
            "city": "Mumbai",
            "gstin": "27AAAAA0000A1Z5",
            "payout_info": {"bank": "HDFC", "account": "12345"},
        }

        self.client.force_authenticate(user=None)
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["name"], "Test Vendor")
        self.assertFalse(response.data["is_active"])

        vendor = Vendor.objects.get(id=response.data["id"])
        self.assertEqual(vendor.name, "Test Vendor")
        self.assertFalse(vendor.is_active)

    def test_create_listing_valid_price(self):
        """Test creating listing with valid pricing"""
        url = reverse("listing-create")
        data = {
            "vendor": str(self.vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-001",
            "base_price": "100.00",
            "mrp": "125.00",  # 25% markup, within 30% limit
            "lead_time_days": 7,
            "enabled": True,
        }

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-key-123"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "SHIRT-001")
        self.assertEqual(Decimal(response.data["mrp"]), Decimal("125.00"))

    def test_create_listing_invalid_price(self):
        """Test creating listing with invalid pricing (exceeds cap)"""
        url = reverse("listing-create")
        data = {
            "vendor": str(self.vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-002",
            "base_price": "100.00",
            "mrp": "150.00",  # 50% markup, exceeds 30% limit
            "lead_time_days": 7,
            "enabled": True,
        }

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-key-456"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("MRP exceeds maximum", str(response.data))

    def test_create_listing_without_approval(self):
        """Test creating listing without vendor approval"""
        # Create new vendor without approval for this test
        new_user = User.objects.create_user(
            email="newvendor@example.com", password="password123", role="vendor"
        )
        vendor = Vendor.objects.create(
            name="New Test Vendor", city="Mumbai", is_active=True, status="approved", user=new_user
        )

        url = reverse("listing-create")
        data = {
            "vendor": str(vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-003",
            "base_price": "100.00",
            "mrp": "125.00",
            "lead_time_days": 7,
            "enabled": True,
        }

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-key-789"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("approved", str(response.data).lower())

    def test_create_listing_inactive_vendor(self):
        """Test creating listing with inactive vendor"""
        # Create inactive vendor for this test
        inactive_user = User.objects.create_user(
            email="inactive@example.com", password="password123", role="vendor"
        )
        vendor = Vendor.objects.create(
            name="Inactive Vendor", city="Mumbai", is_active=False, status="pending", user=inactive_user
        )

        VendorApproval.objects.create(
            vendor=vendor, school=self.school, status="approved"
        )

        url = reverse("listing-create")
        data = {
            "vendor": str(vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-004",
            "base_price": "100.00",
            "mrp": "125.00",
            "lead_time_days": 7,
            "enabled": True,
        }

        response = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-key-abc"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("approved", str(response.data).lower())

    def test_idempotency(self):
        """Test idempotency key works"""
        url = reverse("listing-create")
        data = {
            "vendor": str(self.vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-005",
            "base_price": "100.00",
            "mrp": "125.00",
            "lead_time_days": 7,
            "enabled": True,
        }

        # First request
        response1 = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-idem-123"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second request with same key
        response2 = self.client.post(
            url, data, format="json", HTTP_IDEMPOTENCY_KEY="test-idem-123"
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["id"], response2.data["id"])

    def test_vendor_listings(self):
        """Test getting vendor listings"""
        # Create listing for this test
        listing = Listing.objects.create(
            vendor=self.vendor,
            school=self.school,
            spec=self.spec,
            sku="SHIRT-TEST-006",
            base_price=Decimal("100.00"),
            mrp=Decimal("125.00"),
            lead_time_days=7,
        )

        url = reverse("vendor-listings", kwargs={"vendor_id": self.vendor.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        # Verify our listing is in the results
        skus = [item["sku"] for item in response.data["results"]]
        self.assertIn("SHIRT-TEST-006", skus)

    def test_missing_idempotency_key(self):
        """Test that missing idempotency key returns error"""
        url = reverse("listing-create")
        data = {
            "vendor": str(self.vendor.id),
            "school": str(self.school.id),
            "spec": str(self.spec.id),
            "sku": "SHIRT-007",
            "base_price": "100.00",
            "mrp": "125.00",
            "lead_time_days": 7,
            "enabled": True,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Idempotency-Key", str(response.data))
