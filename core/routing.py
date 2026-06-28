"""WebSocket URL routing for core real-time features."""

from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
    path("ws/presence/", consumers.PresenceConsumer.as_asgi()),
    path("ws/chat/<int:conversation_id>/", consumers.ChatConsumer.as_asgi()),
]
