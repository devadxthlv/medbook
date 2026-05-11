"""
Appointments forms — booking form for patients.
"""

from django import forms

from .models import Appointment, TIME_SLOT_CHOICES


class AppointmentBookingForm(forms.ModelForm):
    """Form used by patients to book an appointment."""

    class Meta:
        model = Appointment
        fields = ["doctor", "date", "time_slot", "reason"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "time_slot": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Textarea(
                attrs={"rows": 3, "class": "form-control", "placeholder": "Reason for visit…"}
            ),
            "doctor": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time_slot"].choices = [("", "Select a time slot")] + list(
            TIME_SLOT_CHOICES
        )


class AppointmentStatusForm(forms.ModelForm):
    """Minimal form for doctors / admin to update appointment status."""

    class Meta:
        model = Appointment
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }
