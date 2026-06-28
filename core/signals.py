"""Signal handlers for profiles, OAuth metadata, and notifications."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Comment, Follow, Like, Message, Notification, Profile, StoryView, UserStatus


def push_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.recipient_id}",
        {
            "type": "notification.created",
            "payload": {
                "id": notification.pk,
                "sender": notification.sender.username,
                "text": notification.get_text(),
                "url": notification.get_absolute_url(),
                "created_at": notification.created_at.isoformat(),
            },
        },
    )


def create_notification(**kwargs):
    notification = Notification.objects.create(**kwargs)
    push_notification(notification)
    return notification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_and_status(sender, instance, created, **kwargs):
    Profile.objects.get_or_create(user=instance)
    UserStatus.objects.get_or_create(user=instance)


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created and instance.follower_id != instance.following_id:
        create_notification(
            recipient=instance.following,
            sender=instance.follower,
            notification_type=Notification.NotificationType.FOLLOW,
        )


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created and instance.user_id != instance.post.user_id:
        create_notification(
            recipient=instance.post.user,
            sender=instance.user,
            notification_type=Notification.NotificationType.LIKE,
            post=instance.post,
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.user_id != instance.post.user_id:
        create_notification(
            recipient=instance.post.user,
            sender=instance.user,
            notification_type=Notification.NotificationType.COMMENT,
            post=instance.post,
        )


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return
    for recipient in instance.conversation.participants.exclude(pk=instance.sender_id):
        create_notification(
            recipient=recipient,
            sender=instance.sender,
            notification_type=Notification.NotificationType.MESSAGE,
            message=instance,
            conversation=instance.conversation,
        )


@receiver(post_save, sender=StoryView)
def create_story_view_notification(sender, instance, created, **kwargs):
    if created and instance.viewer_id != instance.story.user_id:
        create_notification(
            recipient=instance.story.user,
            sender=instance.viewer,
            notification_type=Notification.NotificationType.STORY_VIEW,
            story=instance.story,
        )


try:
    from allauth.socialaccount.models import SocialAccount

    @receiver(post_save, sender=SocialAccount)
    def sync_google_profile(sender, instance, created, **kwargs):
        if instance.provider != "google":
            return
        user = instance.user
        extra = instance.extra_data or {}
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.google_id = instance.uid
        profile.oauth_avatar_url = extra.get("picture", "")
        profile.save(update_fields=["google_id", "oauth_avatar_url", "updated_at"])
        changed = []
        for field, key in (("first_name", "given_name"), ("last_name", "family_name"), ("email", "email")):
            value = extra.get(key)
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                changed.append(field)
        if changed:
            user.save(update_fields=changed)
except Exception:
    pass
