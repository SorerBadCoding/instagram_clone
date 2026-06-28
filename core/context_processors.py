"""Context values shared by the navigation and notification UI."""

from .models import Message, Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "unread_messages_count": 0,
            "navbar_notifications": [],
        }
    notifications = Notification.objects.filter(recipient=request.user).select_related(
        "sender", "sender__profile", "post", "story", "message", "conversation"
    )
    unread_messages_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()
    return {
        "unread_notifications_count": notifications.filter(is_read=False).count(),
        "unread_messages_count": unread_messages_count,
        "navbar_notifications": notifications[:5],
    }
