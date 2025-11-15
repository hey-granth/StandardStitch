from datetime import date
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import School

User = get_user_model()


class SchoolTests(APITestCase):
    def setUp(self):
        # Clear cache and existing schools for test isolation
        cache.clear()
        School.objects.all().delete()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            role="parent"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_school(self):
        """Test creating a School instance"""
        school = School.objects.create(
            name="Test School",
            city="Mumbai",
            board="CBSE",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )

        self.assertEqual(school.name, "Test School")
        self.assertEqual(school.city, "Mumbai")
        self.assertEqual(school.board, "CBSE")
        self.assertTrue(school.is_active)

    def test_list_schools(self):
        """Test listing schools"""
        School.objects.create(
            name="School A",
            city="Mumbai",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )
        School.objects.create(
            name="School B",
            city="Delhi",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )

        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_school(self):
        """Test retrieving a single school"""
        school = School.objects.create(
            name="Test School",
            city="Mumbai",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )

        url = reverse("school-detail", kwargs={"pk": school.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test School")
        self.assertEqual(response.data["city"], "Mumbai")

    def test_filter_schools_by_city(self):
        """Test filtering schools by city"""
        School.objects.create(
            name="School A",
            city="Mumbai",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )
        School.objects.create(
            name="School B",
            city="Delhi",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )

        url = reverse("school-list")
        response = self.client.get(url, {"city": "Mumbai"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["city"], "Mumbai")

    def test_ordering_by_name(self):
        """Test ordering schools by name"""
        School.objects.create(
            name="Zebra School",
            city="Mumbai",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )
        School.objects.create(
            name="Alpha School",
            city="Mumbai",
            session_start=date(2025, 4, 1),
            session_end=date(2026, 3, 31)
        )

        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "Alpha School")
        self.assertEqual(response.data["results"][1]["name"], "Zebra School")

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access schools"""
        self.client.force_authenticate(user=None)

        url = reverse("school-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

