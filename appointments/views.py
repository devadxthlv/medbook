"""
Appointments views — booking, listing, cancellation, status update, available-slots API.
"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import role_required
from doctors.models import Doctor
from .forms import AppointmentBookingForm, AppointmentStatusForm
from .models import Appointment, TIME_SLOT_CHOICES


@login_required
def book_appointment(request, doctor_pk):
    """Patient books an appointment with a specific doctor."""
    doctor = get_object_or_404(Doctor.objects.select_related("user"), pk=doctor_pk)

    if request.method == "POST":
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            try:
                appointment.full_clean()
                appointment.save()
            except Exception as e:
                messages.error(request, str(e))
                return redirect("appointments:book", doctor_pk=doctor.pk)

            # Send confirmation email
            send_mail(
                subject="Appointment Booking Confirmation — MedBook",
                message=(
                    f"Hi {request.user.first_name},\n\n"
                    f"Your appointment with Dr. {doctor.user.get_full_name()} "
                    f"on {appointment.date} at {appointment.get_time_slot_display()} "
                    f"has been booked successfully.\n\n"
                    f"Status: {appointment.get_status_display()}\n\n"
                    "— The MedBook Team"
                ),
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
            messages.success(
                request,
                f"Appointment booked with Dr. {doctor.user.get_full_name()} "
                f"on {appointment.date} at {appointment.get_time_slot_display()}.",
            )
            return redirect("appointments:my_appointments")
    else:
        form = AppointmentBookingForm(initial={"doctor": doctor.pk})

    return render(
        request,
        "appointments/book_appointment.html",
        {"form": form, "doctor": doctor},
    )


@login_required
def my_appointments(request):
    """List appointments for the logged-in patient."""
    today = datetime.date.today()
    upcoming = Appointment.objects.filter(
        patient=request.user, date__gte=today
    ).exclude(status=Appointment.Status.CANCELLED).select_related("doctor__user")
    past = Appointment.objects.filter(
        patient=request.user, date__lt=today
    ).select_related("doctor__user")
    cancelled = Appointment.objects.filter(
        patient=request.user, status=Appointment.Status.CANCELLED
    ).select_related("doctor__user")

    return render(
        request,
        "appointments/my_appointments.html",
        {"upcoming": upcoming, "past": past, "cancelled": cancelled},
    )


@login_required
def cancel_appointment(request, pk):
    """Patient cancels a pending appointment."""
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    if appointment.status != Appointment.Status.PENDING:
        messages.error(request, "Only pending appointments can be cancelled.")
    else:
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.success(request, "Appointment cancelled successfully.")
    return redirect("appointments:my_appointments")


@role_required("DOCTOR")
def doctor_appointments(request):
    """Doctor views their schedule."""
    doctor = get_object_or_404(Doctor, user=request.user)
    today = datetime.date.today()

    appointments = Appointment.objects.filter(doctor=doctor).select_related("patient")
    upcoming = appointments.filter(date__gte=today).exclude(
        status=Appointment.Status.CANCELLED
    )
    past = appointments.filter(date__lt=today)

    return render(
        request,
        "appointments/doctor_appointments.html",
        {"upcoming": upcoming, "past": past},
    )


@role_required("DOCTOR")
def update_appointment_status(request, pk):
    """Doctor updates appointment status (confirm / complete)."""
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)

    if request.method == "POST":
        form = AppointmentStatusForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Appointment status updated to {appointment.get_status_display()}.",
            )
    return redirect("appointments:doctor_appointments")


def available_slots(request):
    """
    JSON endpoint: returns available time slots for a given doctor and date.
    GET /appointments/available-slots/?doctor_id=1&date=2025-01-15
    """
    doctor_id = request.GET.get("doctor_id")
    date_str = request.GET.get("date")

    if not doctor_id or not date_str:
        return JsonResponse({"error": "doctor_id and date are required"}, status=400)

    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return JsonResponse({"error": "Doctor not found."}, status=404)

    # Check if the date falls on a day the doctor is available
    iso_weekday = date.isoweekday()  # 1=Mon … 7=Sun
    if iso_weekday > 5 or iso_weekday not in doctor.available_days_iso:
        return JsonResponse({"slots": [], "message": "Doctor is not available on this day."})

    # Find already-booked slots for that doctor and date (excluding cancelled)
    booked = set(
        Appointment.objects.filter(
            doctor=doctor,
            date=date,
        )
        .exclude(status=Appointment.Status.CANCELLED)
        .values_list("time_slot", flat=True)
    )

    slots = []
    for value, label in TIME_SLOT_CHOICES:
        slots.append(
            {
                "value": value,
                "label": label,
                "available": value not in booked,
            }
        )

    return JsonResponse({"slots": slots})
