"""
Doctors models — Doctor profile linked to User.
"""

from django.conf import settings
from django.db import models


class Doctor(models.Model):
    """
    Extended profile for users with role=DOCTOR.
    Stores professional information and availability.
    """

    class Specialisation(models.TextChoices):
        GENERAL_PRACTICE = "GP", "General Practice"
        CARDIOLOGY = "CARDIO", "Cardiology"
        DERMATOLOGY = "DERM", "Dermatology"
        NEUROLOGY = "NEURO", "Neurology"
        ORTHOPEDICS = "ORTHO", "Orthopedics"
        PEDIATRICS = "PEDIA", "Pediatrics"
        PSYCHIATRY = "PSYCH", "Psychiatry"
        GYNECOLOGY = "GYNEC", "Gynecology"
        OPHTHALMOLOGY = "OPHTH", "Ophthalmology"
        ENT = "ENT", "ENT (Ear, Nose & Throat)"
        UROLOGY = "URO", "Urology"
        ONCOLOGY = "ONCO", "Oncology"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    specialisation = models.CharField(
        max_length=10,
        choices=Specialisation.choices,
    )
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Available days — BooleanFields for Mon–Fri
    available_monday = models.BooleanField(default=True)
    available_tuesday = models.BooleanField(default=True)
    available_wednesday = models.BooleanField(default=True)
    available_thursday = models.BooleanField(default=True)
    available_friday = models.BooleanField(default=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} — {self.get_specialisation_display()}"

    @property
    def available_days_list(self):
        """Return a list of day names this doctor is available."""
        days = []
        mapping = [
            (self.available_monday, "Monday"),
            (self.available_tuesday, "Tuesday"),
            (self.available_wednesday, "Wednesday"),
            (self.available_thursday, "Thursday"),
            (self.available_friday, "Friday"),
        ]
        for flag, name in mapping:
            if flag:
                days.append(name)
        return days

    @property
    def available_days_iso(self):
        """Return ISO weekday numbers (1=Mon … 5=Fri) the doctor works."""
        nums = []
        for i, flag in enumerate(
            [
                self.available_monday,
                self.available_tuesday,
                self.available_wednesday,
                self.available_thursday,
                self.available_friday,
            ],
            start=1,
        ):
            if flag:
                nums.append(i)
        return nums
