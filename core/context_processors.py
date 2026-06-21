"""
Custom context processors made available to every template.
"""

from .models import Notification


def notifications_context(request):
    """
    Adds the current user's unread notification count and the latest
    notifications to every template's context (used for the navbar badge
    and dropdown).
    """
    if request.user.is_authenticated:
        qs = Notification.objects.filter(recipient=request.user).select_related(
            "sender", "sender__profile", "post"
        )
        return {
            "unread_notifications_count": qs.filter(is_read=False).count(),
            "navbar_notifications": qs[:5],
        }
    return {"unread_notifications_count": 0, "navbar_notifications": []}
