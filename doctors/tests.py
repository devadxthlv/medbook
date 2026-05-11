"""
Tests for the doctors app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Doctor

User = get_user_model()


class DoctorListTests(TestCase):
    """Test the public doctor listing page."""

    def setUp(self):
        self.doc_user = User.objects.create_user(
            username="drdoe",
            password="TestPass123!",
            first_name="John",
            last_name="Doe",
            role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            specialisation=Doctor.Specialisation.CARDIOLOGY,
            bio="Expert cardiologist.",
            years_of_experience=10,
            consultation_fee=150.00,
        )

    def test_doctor_list_renders(self):
        response = self.client.get(reverse("doctors:doctor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. John Doe")
        self.assertContains(response, "Cardiology")

    def test_search_filter_by_name(self):
        response = self.client.get(reverse("doctors:doctor_list") + "?q=John")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. John Doe")

    def test_search_filter_no_results(self):
        response = self.client.get(reverse("doctors:doctor_list") + "?q=NonExistent")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No doctors found")

    def test_specialisation_filter(self):
        response = self.client.get(
            reverse("doctors:doctor_list") + "?specialisation=CARDIO"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. John Doe")

    def test_specialisation_filter_empty(self):
        response = self.client.get(
            reverse("doctors:doctor_list") + "?specialisation=NEURO"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No doctors found")


class DoctorDetailTests(TestCase):
    """Test the individual doctor detail page."""

    def setUp(self):
        self.doc_user = User.objects.create_user(
            username="drsmith",
            password="TestPass123!",
            first_name="Sarah",
            last_name="Smith",
            role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            specialisation=Doctor.Specialisation.DERMATOLOGY,
            bio="Board-certified dermatologist.",
            years_of_experience=8,
            consultation_fee=120.00,
        )

    def test_detail_page_renders(self):
        response = self.client.get(
            reverse("doctors:doctor_detail", args=[self.doctor.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sarah Smith")
        self.assertContains(response, "Dermatology")
        self.assertContains(response, "Board-certified")

    def test_detail_404_for_invalid_pk(self):
        response = self.client.get(reverse("doctors:doctor_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)
