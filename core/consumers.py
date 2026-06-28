"""WebSocket consumers for chat, typing, read receipts, presence, and notifications."""

import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Conversation, Message, UserStatus


class AuthenticatedConsumer(AsyncWebsocketConsumer):
    @property
    def user(self):
        return self.scope["user"]

    async def connect(self):
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        await self.accept()


class NotificationConsumer(AuthenticatedConsumer):
    async def connect(self):
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_created(self, event):
        await self.send(text_data=json.dumps({"type": "notification", **event["payload"]}))


class PresenceConsumer(AuthenticatedConsumer):
    async def connect(self):
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        await self.set_presence(True)
        await self.channel_layer.group_add("presence", self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            "presence",
            {"type": "presence.changed", "user_id": self.user.id, "username": self.user.username, "online": True},
        )

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.set_presence(False)
            await self.channel_layer.group_discard("presence", self.channel_name)
            await self.channel_layer.group_send(
                "presence",
                {"type": "presence.changed", "user_id": self.user.id, "username": self.user.username, "online": False},
            )

    async def presence_changed(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def set_presence(self, online):
        UserStatus.objects.update_or_create(
            user=self.user,
            defaults={"is_online": online, "last_seen": timezone.now(), "channel_name": self.channel_name},
        )


class ChatConsumer(AuthenticatedConsumer):
    async def connect(self):
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        allowed = await self.user_can_access()
        if not allowed:
            await self.close(code=4003)
            return
        self.group_name = f"conversation_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        event_type = data.get("type")
        if event_type == "message":
            message = await self.create_message(data.get("content", ""))
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.message",
                    "id": message["id"],
                    "sender": self.user.username,
                    "sender_id": self.user.id,
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                },
            )
        elif event_type == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.typing",
                    "sender": self.user.username,
                    "sender_id": self.user.id,
                    "is_typing": bool(data.get("is_typing")),
                },
            )
        elif event_type == "read":
            await self.mark_read()
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.read", "reader_id": self.user.id, "reader": self.user.username},
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type": "message", **event}))

    async def chat_typing(self, event):
        if event["sender_id"] != self.user.id:
            await self.send(text_data=json.dumps({"type": "typing", **event}))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps({"type": "read", **event}))

    @sync_to_async
    def user_can_access(self):
        return Conversation.objects.filter(pk=self.conversation_id, participants=self.user).exists()

    @sync_to_async
    def create_message(self, content):
        conversation = Conversation.objects.get(pk=self.conversation_id, participants=self.user)
        message = Message.objects.create(conversation=conversation, sender=self.user, content=content.strip())
        Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
        return {"id": message.pk, "content": message.content, "timestamp": message.timestamp.isoformat()}

    @sync_to_async
    def mark_read(self):
        Message.objects.filter(conversation_id=self.conversation_id, is_read=False).exclude(sender=self.user).update(
            is_read=True,
            read_at=timezone.now(),
        )
