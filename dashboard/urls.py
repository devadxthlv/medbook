"""
Dashboard URL patterns.
"""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("users/", views.user_list, name="user_list"),
    path("users/<int:pk>/toggle-active/", views.toggle_user_active, name="toggle_user_active"),
    path("doctors/", views.doctor_management, name="doctor_management"),
    path("doctors/create/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),
    path("appointments/", views.appointment_management, name="appointment_management"),
    path(
        "appointments/<int:pk>/update/",
        views.admin_update_appointment,
        name="admin_update_appointment",
    ),
]
