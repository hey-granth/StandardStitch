from datetime import date
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import School

User = get_user_model()


class SchoolTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.user = User.objects.create_user(
            email="test@example.com", password="password123", role="parent"
        )

        # Create schools for multiple tests
        cls.school_a = School.objects.create(
            name="School A",
            code="SCH-A",
            city="Mumbai",
            address="123 Test St",
            board="CBSE",
            academic_year="2025-2026",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31),
        )

        cls.school_b = School.objects.create(
            name="School B",
            code="SCH-B",
            city="Delhi",
            address="456 Test Ave",
            board="ICSE",
            academic_year="2025-2026",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31),
        )

    def setUp(self):
        """Per-test setup - only authenticate and clear cache"""
        cache.clear()
        self.client.force_authenticate(user=self.user)

    def test_create_school(self):
        """Test that School instances were created correctly"""
        self.assertEqual(self.school_a.name, "School A")
        self.assertEqual(self.school_a.city, "Mumbai")
        self.assertEqual(self.school_a.board, "CBSE")
        self.assertTrue(self.school_a.is_active)

    def test_list_schools(self):
        """Test listing schools"""
        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_retrieve_school(self):
        """Test retrieving a single school"""
        url = reverse("school-detail", kwargs={"pk": self.school_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "School A")
        self.assertEqual(response.data["city"], "Mumbai")

    def test_filter_schools_by_city(self):
        """Test filtering schools by city"""
        url = reverse("school-list")
        response = self.client.get(url, {"city": "Mumbai"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        for school in response.data["results"]:
            self.assertEqual(school["city"], "Mumbai")

    def test_ordering_by_name(self):
        """Test ordering schools by name"""
        # Create additional schools to test ordering
        School.objects.create(
            name="Zebra School",
            code="SCH-Z",
            city="Mumbai",
            address="789 Test Blvd",
            academic_year="2025-2026",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31),
        )
        School.objects.create(
            name="Alpha School",
            code="SCH-ALPHA",
            city="Mumbai",
            address="101 Test Ln",
            academic_year="2025-2026",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31),
        )

        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that schools are ordered by name
        school_names = [school["name"] for school in response.data["results"]]
        self.assertIn("Alpha School", school_names)
        self.assertIn("Zebra School", school_names)
        # Verify ordering: Alpha should come before Zebra
        alpha_index = school_names.index("Alpha School")
        zebra_index = school_names.index("Zebra School")
        self.assertLess(alpha_index, zebra_index)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access schools"""
        self.client.force_authenticate(user=None)

        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
