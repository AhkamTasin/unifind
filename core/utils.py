"""Helper utilities: tracking ID generation, notifications, image helpers."""
import secrets
import string

from django.utils import timezone

from .models import Notification

TRACKING_ID_PREFIX = "LF"

# Store cards are generated once per session if not set elsewhere
_ALPHABET = string.ascii_uppercase + string.digits


def generate_tracking_id():
    """Generate a unique tracking ID like LF-2026-4K7QX9.

    The proposal (FR-08) requires a unique tracking ID for every verified
    found item. Uniqueness is enforced by the DB unique constraint as well.
    """
    now = timezone.localtime()
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(6))
    return f"{TRACKING_ID_PREFIX}-{now.year}-{suffix}"


def notify(user, title, message="", link=""):
    """Create an in-app notification for a user."""
    return Notification.objects.create(
        user=user, title=title, message=message, link=link
    )


def notify_admin(sender, title, message="", link=""):
    """Notify every admin account."""
    from .models import User

    for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True).exclude(pk=sender.pk):
        notify(admin, title, message, link)


def valid_image_file(file_obj):
    """Very light client-side style validation fallback (extension check)."""
    if not file_obj:
        return True
    allowed = {"png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"}
    name = (file_obj.name or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    return ext in allowed
