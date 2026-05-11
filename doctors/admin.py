from django.contrib import admin

from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "specialisation",
        "years_of_experience",
        "consultation_fee",
    )
    list_filter = ("specialisation",)
    search_fields = ("user__first_name", "user__last_name", "user__username")
