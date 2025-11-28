from datetime import date
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from schools.models import School
from .models import UniformSpec

User = get_user_model()


class CatalogTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.user = User.objects.create_user(
            email="test@example.com", password="password123", role="parent"
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

        # Create specs for multiple tests
        cls.spec_shirt_boys = UniformSpec.objects.create(
            school=cls.school,
            academic_year="2025-2026",
            description="Test Description",
            item_type="shirt",
            item_name="Test Shirt",
            gender="boys",
            season="summer",
            fabric_gsm=180,
            pantone="PMS 287C",
            measurements={"chest": "36", "length": "28"},
            version=1,
        )

        cls.spec_pants = UniformSpec.objects.create(
            school=cls.school,
            academic_year="2025-2026",
            description="Test Description",
            item_type="pants",
            item_name="Test Pants",
            gender="boys",
            season="summer",
            fabric_gsm=220,
            pantone="PMS 288C",
            measurements={},
            version=1,
        )

        cls.spec_shirt_girls = UniformSpec.objects.create(
            school=cls.school,
            academic_year="2025-2026",
            description="Test Description",
            item_type="shirt",
            item_name="Test Shirt",
            gender="girls",
            season="summer",
            fabric_gsm=180,
            pantone="PMS 287C",
            measurements={},
            version=1,
        )

    def setUp(self):
        """Per-test setup - only clear cache, don't recreate objects"""
        cache.clear()
        self.client.force_authenticate(user=self.user)

    def test_create_uniform_spec(self):
        """Test creating a UniformSpec instance"""
        self.assertEqual(self.spec_shirt_boys.item_type, "shirt")
        self.assertEqual(self.spec_shirt_boys.school, self.school)
        self.assertEqual(self.spec_shirt_boys.fabric_gsm, 180)
        self.assertEqual(self.spec_shirt_boys.measurements["chest"], "36")
        self.assertFalse(self.spec_shirt_boys.frozen)
        self.assertEqual(self.spec_shirt_boys.version, 1)

    def test_catalog_list(self):
        """Test listing catalog for a school"""
        url = reverse("school-catalog", kwargs={"school_id": self.school.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have 3 items from setUpTestData
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_catalog_filter_by_item_type(self):
        """Test filtering catalog by item_type"""
        url = reverse("school-catalog", kwargs={"school_id": self.school.id})
        response = self.client.get(url, {"item_type": "shirt"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        for item in response.data["results"]:
            self.assertEqual(item["item_type"], "shirt")

    def test_catalog_filter_by_gender(self):
        """Test filtering catalog by gender"""
        url = reverse("school-catalog", kwargs={"school_id": self.school.id})
        response = self.client.get(url, {"gender": "girls"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        for item in response.data["results"]:
            self.assertEqual(item["gender"], "girls")

    def test_catalog_cached(self):
        """Test that catalog responses are cached"""

        url = reverse("school-catalog", kwargs={"school_id": self.school.id})

        # First request - hits database
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second request - should come from cache
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

    def test_catalog_unauthenticated(self):
        """Test that unauthenticated users cannot access catalog"""
        self.client.force_authenticate(user=None)

        url = reverse("school-catalog", kwargs={"school_id": self.school.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_catalog_nonexistent_school(self):
        """Test catalog for non-existent school returns 404"""
        import uuid

        fake_school_id = uuid.uuid4()

        url = reverse("school-catalog", kwargs={"school_id": fake_school_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
