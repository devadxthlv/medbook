"""
Dashboard views — admin-only dashboard with stats, user management,
doctor management, and appointment management.
"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from appointments.models import Appointment
from doctors.models import Doctor
from doctors.forms import DoctorForm


def admin_required(view_func):
    """Decorator: requires user to be staff or have ADMIN role."""
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or request.user.role == "ADMIN"):
            return HttpResponseForbidden("Admin access required.")
        return view_func(request, *args, **kwargs)
    _wrapped.__name__ = view_func.__name__
    _wrapped.__doc__ = view_func.__doc__
    return _wrapped


@admin_required
def dashboard_home(request):
    """Main admin dashboard with summary statistics."""
    today = datetime.date.today()

    total_patients = User.objects.filter(role=User.Role.PATIENT).count()
    total_doctors = Doctor.objects.count()
    appointments_today = Appointment.objects.filter(date=today).count()
    pending_appointments = Appointment.objects.filter(
        status=Appointment.Status.PENDING
    ).count()

    recent_appointments = (
        Appointment.objects.select_related("patient", "doctor__user")
        .order_by("-created_at")[:10]
    )

    context = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "appointments_today": appointments_today,
        "pending_appointments": pending_appointments,
        "recent_appointments": recent_appointments,
    }
    return render(request, "dashboard/home.html", context)


@admin_required
def user_list(request):
    """List all users with role filter."""
    users = User.objects.all().order_by("-date_joined")
    role_filter = request.GET.get("role", "").strip()
    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 20)
    page = request.GET.get("page")
    users_page = paginator.get_page(page)

    context = {
        "users": users_page,
        "role_filter": role_filter,
        "roles": User.Role.choices,
    }
    return render(request, "dashboard/user_list.html", context)


@admin_required
def toggle_user_active(request, pk):
    """Activate or deactivate a user."""
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} has been {status}.")
    return redirect("dashboard:user_list")


@admin_required
def doctor_management(request):
    """List all doctors for management."""
    doctors = Doctor.objects.select_related("user").all()
    return render(request, "dashboard/doctor_list.html", {"doctors": doctors})


@admin_required
def doctor_create(request):
    """Create a new doctor profile — first create a user, then attach Doctor profile."""
    if request.method == "POST":
        # Get user details from the form
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "").strip()

        if not all([username, email, first_name, last_name, password]):
            messages.error(request, "All user fields are required.")
            return redirect("dashboard:doctor_create")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("dashboard:doctor_create")

        form = DoctorForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=User.Role.DOCTOR,
            )
            doctor = form.save(commit=False)
            doctor.user = user
            doctor.save()
            messages.success(request, f"Doctor {user.get_full_name()} created successfully.")
            return redirect("dashboard:doctor_management")
    else:
        form = DoctorForm()

    return render(request, "dashboard/doctor_form.html", {"form": form, "action": "Create"})


@admin_required
def doctor_edit(request, pk):
    """Edit an existing doctor profile."""
    doctor = get_object_or_404(Doctor.objects.select_related("user"), pk=pk)

    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Doctor {doctor.user.get_full_name()} updated.")
            return redirect("dashboard:doctor_management")
    else:
        form = DoctorForm(instance=doctor)

    return render(request, "dashboard/doctor_form.html", {"form": form, "doctor": doctor, "action": "Edit"})


@admin_required
def doctor_delete(request, pk):
    """Delete a doctor profile (and optionally their user account)."""
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        name = str(doctor)
        doctor.user.delete()  # cascades to Doctor
        messages.success(request, f"{name} has been removed.")
    return redirect("dashboard:doctor_management")


@admin_required
def appointment_management(request):
    """List all appointments with filtering."""
    appointments = Appointment.objects.select_related(
        "patient", "doctor__user"
    ).order_by("-date", "-time_slot")

    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    paginator = Paginator(appointments, 20)
    page = request.GET.get("page")
    appointments_page = paginator.get_page(page)

    context = {
        "appointments": appointments_page,
        "status_filter": status_filter,
        "statuses": Appointment.Status.choices,
    }
    return render(request, "dashboard/appointment_list.html", context)


@admin_required
def admin_update_appointment(request, pk):
    """Admin updates an appointment's status."""
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Appointment.Status.choices):
            appointment.status = new_status
            appointment.save()
            messages.success(
                request,
                f"Appointment #{appointment.pk} status updated to {appointment.get_status_display()}.",
            )
    return redirect("dashboard:appointment_management")
