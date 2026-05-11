"""
Tests for the appointments app.
"""

import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from doctors.models import Doctor
from .models import Appointment

User = get_user_model()


class AppointmentBookingTests(TestCase):
    """Test appointment creation and validation."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient1",
            password="TestPass123!",
            first_name="Alice",
            last_name="Wonder",
            role=User.Role.PATIENT,
        )
        self.doc_user = User.objects.create_user(
            username="doctor1",
            password="TestPass123!",
            first_name="Bob",
            last_name="Builder",
            role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            specialisation=Doctor.Specialisation.GENERAL_PRACTICE,
            years_of_experience=5,
            consultation_fee=100,
        )
        self.tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        # Ensure tomorrow is a weekday; if Saturday, push to Monday
        while self.tomorrow.isoweekday() > 5:
            self.tomorrow += datetime.timedelta(days=1)

    def test_booking_creates_record(self):
        self.client.login(username="patient1", password="TestPass123!")
        response = self.client.post(
            reverse("appointments:book", args=[self.doctor.pk]),
            {
                "doctor": self.doctor.pk,
                "date": self.tomorrow.isoformat(),
                "time_slot": "09:00",
                "reason": "General checkup",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 1)
        appt = Appointment.objects.first()
        self.assertEqual(appt.patient, self.patient)
        self.assertEqual(appt.doctor, self.doctor)
        self.assertEqual(appt.status, Appointment.Status.PENDING)

    def test_double_booking_prevented_at_db_level(self):
        """DB-level unique constraint prevents identical (doctor, date, time_slot)."""
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="09:00",
            reason="First",
        )
        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                date=self.tomorrow,
                time_slot="09:00",
                reason="Duplicate",
            )

    def test_cancellation_changes_status(self):
        self.client.login(username="patient1", password="TestPass123!")
        appt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="10:00",
            status=Appointment.Status.PENDING,
        )
        response = self.client.post(
            reverse("appointments:cancel", args=[appt.pk])
        )
        self.assertEqual(response.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.CANCELLED)

    def test_cancel_non_pending_fails(self):
        self.client.login(username="patient1", password="TestPass123!")
        appt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="11:00",
            status=Appointment.Status.CONFIRMED,
        )
        response = self.client.post(
            reverse("appointments:cancel", args=[appt.pk])
        )
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.CONFIRMED)


class AvailableSlotsAPITests(TestCase):
    """Test the available-slots JSON endpoint."""

    def setUp(self):
        self.doc_user = User.objects.create_user(
            username="slotdoc",
            password="TestPass123!",
            role=User.Role.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            specialisation=Doctor.Specialisation.GENERAL_PRACTICE,
            years_of_experience=3,
            consultation_fee=80,
        )
        self.patient = User.objects.create_user(
            username="slotpatient",
            password="TestPass123!",
            role=User.Role.PATIENT,
        )
        self.weekday = datetime.date.today() + datetime.timedelta(days=1)
        while self.weekday.isoweekday() > 5:
            self.weekday += datetime.timedelta(days=1)

    def test_available_slots_returns_json(self):
        response = self.client.get(
            reverse("appointments:available_slots"),
            {"doctor_id": self.doctor.pk, "date": self.weekday.isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("slots", data)
        self.assertTrue(len(data["slots"]) > 0)

    def test_booked_slot_marked_unavailable(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.weekday,
            time_slot="09:00",
        )
        response = self.client.get(
            reverse("appointments:available_slots"),
            {"doctor_id": self.doctor.pk, "date": self.weekday.isoformat()},
        )
        data = response.json()
        slot_0900 = next(s for s in data["slots"] if s["value"] == "09:00")
        self.assertFalse(slot_0900["available"])

    def test_missing_params_returns_400(self):
        response = self.client.get(reverse("appointments:available_slots"))
        self.assertEqual(response.status_code, 400)
