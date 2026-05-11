"""
Doctors views — public listing, detail, and admin CRUD.
"""

from django.db import models as db_models
from django.shortcuts import get_object_or_404, render

from .models import Doctor


def doctor_list(request):
    """Public doctor listing with search and specialisation filter."""
    doctors = Doctor.objects.select_related("user").all()

    query = request.GET.get("q", "").strip()
    specialisation = request.GET.get("specialisation", "").strip()

    if query:
        doctors = doctors.filter(
            db_models.Q(user__first_name__icontains=query)
            | db_models.Q(user__last_name__icontains=query)
        )
    if specialisation:
        doctors = doctors.filter(specialisation=specialisation)

    context = {
        "doctors": doctors,
        "query": query,
        "specialisation": specialisation,
        "specialisations": Doctor.Specialisation.choices,
    }
    return render(request, "doctors/doctor_list.html", context)


def doctor_detail(request, pk):
    """Individual doctor profile page."""
    doctor = get_object_or_404(Doctor.objects.select_related("user"), pk=pk)
    return render(request, "doctors/doctor_detail.html", {"doctor": doctor})
