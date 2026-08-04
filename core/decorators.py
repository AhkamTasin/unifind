"""Role-based access decorators."""
from django.contrib.auth.decorators import user_passes_test


def user_is_admin(user):
    return user.is_authenticated and getattr(user, "role", None) == "ADMIN"


def admin_required(view_func):
    """Only allow users with the ADMIN role to access a view."""
    return user_passes_test(user_is_admin, login_url="login", redirect_field_name=None)(
        view_func
    )
