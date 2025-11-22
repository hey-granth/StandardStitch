"""
Tests for vendor onboarding and role-based access control.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from vendors.models import Vendor


class VendorFlowTests(APITestCase):
    """Test vendor onboarding, approval, and permission flow"""

    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        # Parent user
        cls.parent_user = User.objects.create_user(
            email="parent@example.com", password="password123", role="parent"
        )

        # Ops user
        cls.ops_user = User.objects.create_user(
            email="ops@example.com", password="password123", role="ops", is_staff=True
        )

        # Another parent for testing
        cls.parent2_user = User.objects.create_user(
            email="parent2@example.com", password="password123", role="parent"
        )

    def test_signup_defaults_to_parent_role(self):
        """Test that signup always creates user with 'parent' role"""
        url = reverse("signup")
        data = {
            "email": "newuser@example.com",
            "password": "password123",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["role"], "parent")

        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.role, "parent")

    def test_signup_ignores_role_field(self):
        """Test that signup ignores any role field sent in request"""
        url = reverse("signup")
        data = {
            "email": "hacker@example.com",
            "password": "password123",
            "role": "ops",  # Try to set ops role
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Should still be parent, not ops
        self.assertEqual(response.data["user"]["role"], "parent")

    def test_vendor_onboard_requires_parent_role(self):
        """Test that only users with 'parent' role can onboard as vendors"""
        self.client.force_authenticate(user=self.parent_user)

        url = reverse("vendor-onboard")
        data = {
            "gst_number": "29ABCDE1234F1Z5",
            "official_name": "Test Vendor Pvt Ltd",
            "email": "vendor@example.com",
            "phone": "9876543210",
            "city": "Mumbai",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["gst_number"], "29ABCDE1234F1Z5")

    def test_vendor_onboard_creates_pending_status(self):
        """Test that vendor onboarding creates vendor with 'pending' status"""
        self.client.force_authenticate(user=self.parent_user)

        url = reverse("vendor-onboard")
        data = {
            "gst_number": "29ABCDE1234F1Z5",
            "official_name": "Test Vendor Pvt Ltd",
            "email": "vendor@example.com",
            "phone": "9876543210",
            "city": "Mumbai",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        vendor = Vendor.objects.get(user=self.parent_user)
        self.assertEqual(vendor.status, "pending")
        self.assertFalse(vendor.is_active)

        # User role should still be parent
        self.parent_user.refresh_from_db()
        self.assertEqual(self.parent_user.role, "parent")

    def test_vendor_onboard_validates_gst_format(self):
        """Test GST number format validation"""
        self.client.force_authenticate(user=self.parent_user)

        url = reverse("vendor-onboard")
        data = {
            "gst_number": "INVALID",
            "official_name": "Test Vendor",
            "email": "vendor@example.com",
            "phone": "9876543210",
            "city": "Mumbai",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gst_number", response.data)

    def test_vendor_onboard_rejects_duplicate_gst(self):
        """Test that duplicate GST numbers are rejected"""
        # Create first vendor
        Vendor.objects.create(
            user=self.parent2_user,
            gst_number="29ABCDE1234F1Z5",
            official_name="First Vendor",
            email="vendor1@example.com",
            phone="1111111111",
            city="Mumbai",
            status="pending",
        )

        # Try to create another with same GST
        self.client.force_authenticate(user=self.parent_user)
        url = reverse("vendor-onboard")
        data = {
            "gst_number": "29ABCDE1234F1Z5",
            "official_name": "Second Vendor",
            "email": "vendor2@example.com",
            "phone": "2222222222",
            "city": "Delhi",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendor_approve_sets_status_and_role(self):
        """Test that approving vendor sets status='approved' and user.role='vendor'"""
        # Create pending vendor
        vendor = Vendor.objects.create(
            user=self.parent_user,
            gst_number="29ABCDE1234F1Z5",
            official_name="Test Vendor",
            email="vendor@example.com",
            phone="9876543210",
            city="Mumbai",
            status="pending",
        )

        # Approve as ops user
        self.client.force_authenticate(user=self.ops_user)
        url = reverse("vendor-approve", kwargs={"vendor_id": vendor.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        vendor.refresh_from_db()
        self.assertEqual(vendor.status, "approved")
        self.assertTrue(vendor.is_active)

        # Check user role changed to vendor
        self.parent_user.refresh_from_db()
        self.assertEqual(self.parent_user.role, "vendor")

    def test_vendor_approve_requires_ops_or_staff(self):
        """Test that only ops/staff can approve vendors"""
        vendor = Vendor.objects.create(
            user=self.parent_user,
            gst_number="29ABCDE1234F1Z5",
            official_name="Test Vendor",
            email="vendor@example.com",
            phone="9876543210",
            city="Mumbai",
            status="pending",
        )

        # Try to approve as parent user
        self.client.force_authenticate(user=self.parent2_user)
        url = reverse("vendor-approve", kwargs={"vendor_id": vendor.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_list_requires_ops_or_staff(self):
        """Test that only ops/staff can list all vendors"""
        # Try as parent user
        self.client.force_authenticate(user=self.parent_user)
        url = reverse("vendor-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as ops user
        self.client.force_authenticate(user=self.ops_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_me_returns_own_profile(self):
        """Test that /vendors/me returns current user's vendor profile"""
        vendor = Vendor.objects.create(
            user=self.parent_user,
            gst_number="29ABCDE1234F1Z5",
            official_name="Test Vendor",
            email="vendor@example.com",
            phone="9876543210",
            city="Mumbai",
            status="pending",
        )

        self.client.force_authenticate(user=self.parent_user)
        url = reverse("vendor-me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(vendor.id))
        self.assertEqual(response.data["gst_number"], "29ABCDE1234F1Z5")

    def test_vendor_me_returns_404_if_no_profile(self):
        """Test that /vendors/me returns 404 if user has no vendor profile"""
        self.client.force_authenticate(user=self.parent2_user)
        url = reverse("vendor-me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_helper_methods(self):
        """Test User model helper methods"""
        parent = User.objects.create_user(
            email="parent@test.com", password="pass", role="parent"
        )
        vendor = User.objects.create_user(
            email="vendor@test.com", password="pass", role="vendor"
        )
        admin = User.objects.create_user(
            email="admin@test.com", password="pass", role="school_admin"
        )
        ops = User.objects.create_user(
            email="ops@test.com", password="pass", role="ops"
        )

        # Test parent
        self.assertFalse(parent.is_vendor())
        self.assertFalse(parent.is_school_admin())
        self.assertFalse(parent.is_ops())

        # Test vendor
        self.assertTrue(vendor.is_vendor())
        self.assertFalse(vendor.is_school_admin())
        self.assertFalse(vendor.is_ops())

        # Test school_admin
        self.assertFalse(admin.is_vendor())
        self.assertTrue(admin.is_school_admin())
        self.assertFalse(admin.is_ops())

        # Test ops
        self.assertFalse(ops.is_vendor())
        self.assertFalse(ops.is_school_admin())
        self.assertTrue(ops.is_ops())

    def test_complete_vendor_flow(self):
        """Test complete flow: signup -> onboard -> approve -> role change"""
        # 1. Signup as parent
        signup_url = reverse("signup")
        signup_data = {
            "email": "newvendor@example.com",
            "password": "password123",
        }
        signup_response = self.client.post(signup_url, signup_data)
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(signup_response.data["user"]["role"], "parent")

        new_user = User.objects.get(email="newvendor@example.com")

        # 2. Onboard as vendor (still parent role)
        self.client.force_authenticate(user=new_user)
        onboard_url = reverse("vendor-onboard")
        onboard_data = {
            "gst_number": "27ABCDE9999F1Z9",
            "official_name": "New Vendor Ltd",
            "email": "contact@newvendor.com",
            "phone": "9999999999",
            "city": "Bangalore",
        }
        onboard_response = self.client.post(onboard_url, onboard_data)
        self.assertEqual(onboard_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(onboard_response.data["status"], "pending")

        new_user.refresh_from_db()
        self.assertEqual(new_user.role, "parent")  # Still parent

        vendor = Vendor.objects.get(user=new_user)

        # 3. Admin approves vendor
        self.client.force_authenticate(user=self.ops_user)
        approve_url = reverse("vendor-approve", kwargs={"vendor_id": vendor.id})
        approve_response = self.client.post(approve_url)
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        # 4. Verify role changed to vendor
        new_user.refresh_from_db()
        vendor.refresh_from_db()
        self.assertEqual(new_user.role, "vendor")
        self.assertEqual(vendor.status, "approved")
        self.assertTrue(vendor.is_active)
