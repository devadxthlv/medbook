"""
Accounts views — registration, profile, and custom login/logout.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import PatientRegistrationForm, CustomLoginForm, ProfileUpdateForm


def register(request):
    """Patient self-registration."""
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send a welcome / confirmation email (console backend in dev)
            send_mail(
                subject="Welcome to MedBook!",
                message=(
                    f"Hi {user.first_name},\n\n"
                    "Your account has been created successfully. "
                    "You can now log in and book appointments with our doctors.\n\n"
                    "— The MedBook Team"
                ),
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=True,
            )
            login(request, user)
            messages.success(request, "Registration successful! Welcome to MedBook.")
            return redirect("core:home")
    else:
        form = PatientRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


class CustomLoginView(LoginView):
    """Login view using our Bootstrap-styled form."""

    template_name = "accounts/login.html"
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Log the user out and redirect to home."""

    next_page = "/"


@login_required
def profile(request):
    """View and update user profile."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    success_url = "/accounts/password-reset/done/"


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = "/accounts/password-reset/complete/"


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
