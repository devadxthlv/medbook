"""
Shared decorators for role-based access control.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Decorator that checks the authenticated user's role against a whitelist.

    Usage:
        @role_required('ADMIN')
        def admin_only_view(request): ...

        @role_required('DOCTOR', 'ADMIN')
        def doctor_or_admin_view(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden(
                    "You do not have permission to access this page."
                )
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
