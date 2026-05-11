"""
Tests for the dashboard app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardAccessTests(TestCase):
    """Only admins / staff can access the dashboard."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adminuser",
            password="AdminPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.patient = User.objects.create_user(
            username="patientuser",
            password="PatientPass123!",
            role=User.Role.PATIENT,
        )
        self.doctor_user = User.objects.create_user(
            username="doctoruser",
            password="DoctorPass123!",
            role=User.Role.DOCTOR,
        )

    def test_admin_can_access_dashboard(self):
        self.client.login(username="adminuser", password="AdminPass123!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_patient_gets_forbidden(self):
        self.client.login(username="patientuser", password="PatientPass123!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 403)

    def test_doctor_gets_forbidden(self):
        self.client.login(username="doctoruser", password="DoctorPass123!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_user_list_admin_only(self):
        self.client.login(username="adminuser", password="AdminPass123!")
        response = self.client.get(reverse("dashboard:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_user_list_forbidden_for_patient(self):
        self.client.login(username="patientuser", password="PatientPass123!")
        response = self.client.get(reverse("dashboard:user_list"))
        self.assertEqual(response.status_code, 403)
