"""
Doctors forms — used by admin to create / edit doctor profiles.
"""

from django import forms

from .models import Doctor


class DoctorForm(forms.ModelForm):
    """Form for creating/editing a doctor profile."""

    class Meta:
        model = Doctor
        fields = [
            "specialisation",
            "bio",
            "years_of_experience",
            "consultation_fee",
            "available_monday",
            "available_tuesday",
            "available_wednesday",
            "available_thursday",
            "available_friday",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "specialisation": forms.Select(attrs={"class": "form-select"}),
            "years_of_experience": forms.NumberInput(attrs={"class": "form-control"}),
            "consultation_fee": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style checkbox fields
        for day_field in [
            "available_monday",
            "available_tuesday",
            "available_wednesday",
            "available_thursday",
            "available_friday",
        ]:
            self.fields[day_field].widget.attrs.update({"class": "form-check-input"})
