from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("MedBook", {"fields": ("role", "phone", "date_of_birth", "address", "profile_photo")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("MedBook", {"fields": ("role", "email", "first_name", "last_name")}),
    )
