"""
Appointments URL patterns.
"""

from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("book/<int:doctor_pk>/", views.book_appointment, name="book"),
    path("my/", views.my_appointments, name="my_appointments"),
    path("cancel/<int:pk>/", views.cancel_appointment, name="cancel"),
    path("doctor/", views.doctor_appointments, name="doctor_appointments"),
    path(
        "update-status/<int:pk>/",
        views.update_appointment_status,
        name="update_status",
    ),
    path("available-slots/", views.available_slots, name="available_slots"),
]
