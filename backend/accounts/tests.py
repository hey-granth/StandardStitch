from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import User


class AuthTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.existing_user = User.objects.create_user(
            email="existing@example.com", password="password123", role="parent"
        )
        cls.google_user = User.objects.create_user(
            email="google@example.com", role="parent", google_id="google123"
        )

    def test_signup_success(self):
        """Test user signup with email and password"""
        url = reverse("signup")
        data = {
            "email": "test@example.com",
            "password": "password123",
            "role": "parent",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_signup_duplicate_email(self):
        """Test signup with duplicate email"""
        url = reverse("signup")
        data = {"email": "existing@example.com", "password": "password123"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test user login"""
        url = reverse("login")
        data = {"email": "existing@example.com", "password": "password123"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse("login")
        data = {"email": "existing@example.com", "password": "wrongpassword"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.views.id_token.verify_oauth2_token")
    def test_google_auth_new_user(self, mock_verify):
        """Test Google OAuth for new user"""
        mock_verify.return_value = {"sub": "google456", "email": "newgoogle@example.com"}

        url = reverse("google_auth")
        data = {"token": "fake_google_token", "role": "parent"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["created"])
        self.assertTrue(User.objects.filter(email="newgoogle@example.com").exists())

    @patch("accounts.views.id_token.verify_oauth2_token")
    def test_google_auth_existing_user(self, mock_verify):
        """Test Google OAuth for existing user"""

        mock_verify.return_value = {"sub": "google123", "email": "google@example.com"}

        url = reverse("google_auth")
        data = {"token": "fake_google_token"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["created"])

    def test_me_authenticated(self):
        """Test getting current user profile"""
        self.client.force_authenticate(user=self.existing_user)

        url = reverse("me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "existing@example.com")

    def test_me_unauthenticated(self):
        """Test getting profile without authentication"""
        url = reverse("me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserModelTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data once per test class"""
        cls.test_user = User.objects.create_user(
            email="model@example.com", password="password123", role="parent"
        )
        cls.superuser = User.objects.create_superuser(
            email="admin@example.com", password="password123"
        )

    def test_create_user(self):
        """Test user creation"""
        user = User.objects.create_user(
            email="new@example.com", password="password123", role="parent"
        )

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.role, "parent")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("password123"))

    def test_create_superuser(self):
        """Test superuser creation"""
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)
        self.assertEqual(self.superuser.role, "ops")

    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.test_user), "model@example.com")

    def test_email_unique(self):
        """Test email uniqueness"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="model@example.com", password="password456")
