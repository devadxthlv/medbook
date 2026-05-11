"""
Appointments models — Appointment with time-slot system.
"""

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def generate_time_slots():
    """Generate 30-minute slots from 09:00 to 17:00."""
    slots = []
    current = datetime.time(9, 0)
    end = datetime.time(17, 0)
    while current < end:
        label = current.strftime("%I:%M %p")
        slots.append((current.strftime("%H:%M"), label))
        # Advance by 30 minutes
        dt = datetime.datetime.combine(datetime.date.today(), current)
        dt += datetime.timedelta(minutes=30)
        current = dt.time()
    return slots


TIME_SLOT_CHOICES = generate_time_slots()


class Appointment(models.Model):
    """
    A single appointment between a patient and a doctor.
    Unique constraint on (doctor, date, time_slot) prevents double-booking
    at the database level.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_appointments",
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        on_delete=models.CASCADE,
        related_name="doctor_appointments",
    )
    date = models.DateField()
    time_slot = models.CharField(max_length=5, choices=TIME_SLOT_CHOICES)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-time_slot"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time_slot"],
                name="unique_doctor_date_timeslot",
            )
        ]

    def __str__(self):
        return (
            f"Appointment: {self.patient} with {self.doctor} "
            f"on {self.date} at {self.get_time_slot_display()}"
        )

    def clean(self):
        """Validate that the slot is not already booked (form-level check)."""
        if self.date and self.time_slot and self.doctor_id:
            qs = Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time_slot=self.time_slot,
            ).exclude(status=self.Status.CANCELLED)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "This time slot is already booked. Please choose another."
                )
