"""Database models for the production-ready Instagram clone."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


User = settings.AUTH_USER_MODEL


def default_story_expiry():
    return timezone.now() + timedelta(hours=getattr(settings, "STORY_LIFETIME_HOURS", 24))


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        default="defaults/default_avatar.png",
        blank=True,
    )
    oauth_avatar_url = models.URLField(blank=True)
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    show_activity_status = models.BooleanField(default=True)
    allow_story_replies = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["google_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"username": self.user.username})

    @property
    def avatar_url(self):
        default_picture_names = {"", "defaults/default_avatar.png"}
        picture_name = getattr(self.profile_picture, "name", "")
        if self.profile_picture and picture_name not in default_picture_names:
            return self.profile_picture.url
        if self.oauth_avatar_url:
            return self.oauth_avatar_url
        return settings.STATIC_URL + "img/default_avatar.svg"

    @property
    def followers_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def posts_count(self):
        return self.user.posts.count()


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/")
    caption = models.TextField(max_length=2200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Post #{self.pk} by {self.user.username}"

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"pk": self.pk})

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

    def is_liked_by(self, user):
        return bool(user and user.is_authenticated and self.likes.filter(user=user).exists())


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on Post #{self.post_id}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like_per_user_post")
        ]
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["post", "-created_at"])]

    def __str__(self):
        return f"{self.user.username} likes Post #{self.post_id}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_per_pair"),
            models.CheckConstraint(
                condition=~Q(follower=models.F("following")),
                name="prevent_self_follow",
            ),
        ]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["follower", "-created_at"]),
            models.Index(fields=["following", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class StoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(expires_at__gt=timezone.now())

    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(Q(privacy=Story.Privacy.PUBLIC) | Q(user=user))


class Story(models.Model):
    class Privacy(models.TextChoices):
        PUBLIC = "public", "Public"
        FOLLOWERS = "followers", "Followers"
        PRIVATE = "private", "Private"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    image = models.ImageField(upload_to="stories/", blank=True)
    video = models.FileField(upload_to="stories/videos/", blank=True)
    caption = models.CharField(max_length=200, blank=True)
    privacy = models.CharField(max_length=20, choices=Privacy.choices, default=Privacy.FOLLOWERS)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_story_expiry)

    objects = StoryQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Story #{self.pk} by {self.user.username}"

    @property
    def is_active(self):
        return self.expires_at > timezone.now()

    @property
    def media_url(self):
        if self.video:
            return self.video.url
        return self.image.url if self.image else ""

    @property
    def views_count(self):
        return self.views.count()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = default_story_expiry()
        super().save(*args, **kwargs)


class StoryView(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="story_views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["story", "viewer"], name="unique_story_view")
        ]
        ordering = ["-viewed_at"]
        indexes = [
            models.Index(fields=["story", "-viewed_at"]),
            models.Index(fields=["viewer", "-viewed_at"]),
        ]

    def __str__(self):
        return f"{self.viewer} viewed Story #{self.story_id}"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["-updated_at"])]

    def __str__(self):
        return f"Conversation #{self.pk}"

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).select_related("profile").first()

    @classmethod
    def between(cls, user_a, user_b):
        conversation = (
            cls.objects.filter(participants=user_a)
            .filter(participants=user_b)
            .annotate(participant_count=models.Count("participants"))
            .filter(participant_count=2)
            .first()
        )
        if conversation:
            return conversation
        conversation = cls.objects.create()
        conversation.participants.add(user_a, user_b)
        return conversation


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(max_length=2000, blank=True)
    image = models.ImageField(upload_to="messages/", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["conversation", "-timestamp"]),
            models.Index(fields=["sender", "-timestamp"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"Message #{self.pk} from {self.sender.username}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        MESSAGE = "message", "Message"
        STORY_VIEW = "story_view", "Story view"

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["notification_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.notification_type}"

    def get_text(self):
        mapping = {
            self.NotificationType.FOLLOW: "started following you.",
            self.NotificationType.LIKE: "liked your post.",
            self.NotificationType.COMMENT: "commented on your post.",
            self.NotificationType.MESSAGE: "sent you a message.",
            self.NotificationType.STORY_VIEW: "viewed your story.",
        }
        return mapping.get(self.notification_type, "")

    def get_absolute_url(self):
        if self.conversation_id:
            return reverse("conversation_detail", kwargs={"pk": self.conversation_id})
        if self.post_id:
            return reverse("post_detail", kwargs={"pk": self.post_id})
        if self.story_id:
            return reverse("story_viewer", kwargs={"username": self.story.user.username})
        return reverse("profile_detail", kwargs={"username": self.sender.username})


class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    channel_name = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["is_online", "-last_seen"])]

    def __str__(self):
        return f"{self.user.username}: {'online' if self.is_online else 'offline'}"


class RecentSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recent_searches")
    searched_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searched_by")
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "searched_user"], name="unique_recent_user_search")
        ]
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user.username} searched {self.searched_user.username}"
