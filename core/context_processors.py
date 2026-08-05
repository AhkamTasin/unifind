"""Template context processors shared across all pages."""
from .models import Notification


def site_globals(request):
    unread = 0
    if request.user.is_authenticated:
        unread = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    return {
        "unread_notifications": unread,
        "site_name": "UniFind",
    }
