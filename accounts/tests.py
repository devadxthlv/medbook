"""
Tests for the accounts app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    """Test patient self-registration."""

    def test_registration_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Account")

    def test_valid_registration(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newpatient",
                "email": "patient@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "5551234",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)  # redirect after success
        user = User.objects.get(username="newpatient")
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(user.is_active)

    def test_registration_duplicate_username(self):
        User.objects.create_user(username="taken", password="pass12345678")
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "taken",
                "email": "x@example.com",
                "first_name": "A",
                "last_name": "B",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)  # re-renders form with errors


class LoginLogoutTests(TestCase):
    """Test login and logout flows."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPass123!",
            role=User.Role.PATIENT,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_valid_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "TestPass123!"},
        )
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)  # stays on login page

    def test_logout(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)


class ProfileTests(TestCase):
    """Test profile view and update."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="TestPass123!",
            first_name="Old",
            last_name="Name",
            role=User.Role.PATIENT,
        )
        self.client.login(username="profileuser", password="TestPass123!")

    def test_profile_page_loads(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")

    def test_profile_update(self):
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "New",
                "last_name": "Name",
                "email": "new@example.com",
                "phone": "",
                "address": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.email, "new@example.com")


class AccessControlTests(TestCase):
    """Unauthenticated users should be redirected to login."""

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
