"""Views for the Instagram clone."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

try:
    from django_ratelimit.decorators import ratelimit
except Exception:  # pragma: no cover - keeps local dev usable if dependency is absent
    def ratelimit(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

from .forms import (
    CommentForm,
    LoginForm,
    MessageForm,
    NewConversationForm,
    PostForm,
    ProfileForm,
    StoryForm,
    UserRegisterForm,
)
from .models import (
    Comment,
    Conversation,
    Follow,
    Like,
    Message,
    Notification,
    Post,
    Profile,
    RecentSearch,
    Story,
    StoryView,
)


def health_check(request):
    """Simple health check endpoint used by load balancers and platform health checks."""
    from django.http import JsonResponse

    return JsonResponse({"status": "ok"})


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("feed")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f"Welcome to InstaClone, {self.object.username}!")
        return response

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("feed")
        return super().get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


class FeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "core/feed.html"
    context_object_name = "posts"
    paginate_by = getattr(settings, "FEED_PER_PAGE", 6)

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list("following_id", flat=True)
        liked_subquery = Like.objects.filter(post=OuterRef("pk"), user=self.request.user)
        return (
            Post.objects.filter(Q(user_id__in=following_ids) | Q(user=self.request.user))
            .select_related("user", "user__profile")
            .prefetch_related("comments__user", "comments__user__profile", "likes")
            .annotate(
                liked_count=Count("likes", distinct=True),
                comment_count=Count("comments", distinct=True),
                user_has_liked=Exists(liked_subquery),
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        following_ids = list(Follow.objects.filter(follower=self.request.user).values_list("following_id", flat=True))
        story_user_ids = following_ids + [self.request.user.id]
        stories = (
            Story.objects.active()
            .filter(user_id__in=story_user_ids)
            .select_related("user", "user__profile")
            .prefetch_related("views")
            .order_by("user_id", "-created_at")
        )
        grouped = {}
        for story in stories:
            grouped.setdefault(story.user_id, []).append(story)
        ordered_user_ids = [self.request.user.id] + [uid for uid in following_ids if uid in grouped]
        context["story_groups"] = [
            {"user": grouped[uid][0].user, "stories": grouped[uid]}
            for uid in ordered_user_ids
            if uid in grouped
        ]
        context["comment_form"] = CommentForm()
        context["is_feed_empty"] = not context["posts"]
        return context


class ExploreView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "core/explore.html"
    context_object_name = "posts"
    paginate_by = getattr(settings, "POSTS_PER_PAGE", 9)

    def get_queryset(self):
        liked_subquery = Like.objects.filter(post=OuterRef("pk"), user=self.request.user)
        return (
            Post.objects.exclude(user=self.request.user)
            .select_related("user", "user__profile")
            .prefetch_related("comments", "likes")
            .annotate(
                liked_count=Count("likes", distinct=True),
                comment_count=Count("comments", distinct=True),
                user_has_liked=Exists(liked_subquery),
            )
            .order_by("-created_at")
        )


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "core/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.select_related("user", "user__profile").prefetch_related(
            "comments__user", "comments__user__profile", "likes"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("user", "user__profile")
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your post was shared successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("post_detail", kwargs={"pk": self.object.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def test_func(self):
        return self.get_object().user_id == self.request.user.id

    def handle_no_permission(self):
        messages.error(self.request, "You can only edit your own posts.")
        return redirect("feed")

    def get_success_url(self):
        return reverse("post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "core/post_confirm_delete.html"
    success_url = reverse_lazy("feed")

    def test_func(self):
        return self.get_object().user_id == self.request.user.id

    def handle_no_permission(self):
        messages.error(self.request, "You can only delete your own posts.")
        return redirect("feed")


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "core/profile_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        profile, _ = Profile.objects.select_related("user").get_or_create(user=user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object.user
        posts = (
            Post.objects.filter(user=profile_user)
            .prefetch_related("likes", "comments")
            .annotate(liked_count=Count("likes", distinct=True), comment_count=Count("comments", distinct=True))
            .order_by("-created_at")
        )
        context["posts"] = Paginator(posts, getattr(settings, "POSTS_PER_PAGE", 9)).get_page(self.request.GET.get("page"))
        context["is_own_profile"] = profile_user == self.request.user
        context["is_following"] = (
            not context["is_own_profile"]
            and Follow.objects.filter(follower=self.request.user, following=profile_user).exists()
        )
        context["active_stories"] = Story.objects.active().filter(user=profile_user)
        context["mutual_followers"] = User.objects.filter(
            followers__follower=self.request.user,
            following__following=profile_user,
        ).select_related("profile")[:3]
        status = getattr(profile_user, "status", None)
        context["is_online"] = bool(status and status.is_online and profile_user.profile.show_activity_status)
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "core/profile_form.html"

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse("profile_detail", kwargs={"username": self.request.user.username})


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "core/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "sender", "sender__profile", "post", "story", "message", "conversation"
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return response


class SearchView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "core/search.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        if not self.query:
            return Profile.objects.none()
        return (
            Profile.objects.select_related("user")
            .filter(
                Q(user__username__icontains=self.query)
                | Q(user__first_name__icontains=self.query)
                | Q(user__last_name__icontains=self.query)
                | Q(bio__icontains=self.query)
            )
            .order_by("user__username")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        if self.query:
            for profile in context["profiles"][:5]:
                if profile.user != self.request.user:
                    RecentSearch.objects.update_or_create(user=self.request.user, searched_user=profile.user)
        context["recent_searches"] = RecentSearch.objects.filter(user=self.request.user).select_related(
            "searched_user", "searched_user__profile"
        )[:8]
        context["suggested_users"] = Profile.objects.exclude(user=self.request.user).select_related("user")[:8]
        return context


@login_required
def search_suggestions(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query and request.user.is_authenticated:
        profiles = (
            Profile.objects.select_related("user")
            .filter(
                Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(bio__icontains=query)
            )
            .order_by("user__username")[:8]
        )
        for profile in profiles:
            results.append(
                {
                    "username": profile.user.username,
                    "bio": profile.bio[:60],
                    "url": reverse("profile_detail", kwargs={"username": profile.user.username}),
                    "avatar": profile.avatar_url,
                }
            )
    return JsonResponse({"results": results})


class StoryCreateView(LoginRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = "core/story_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your story was posted! It will expire in 24 hours.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("feed")


class StoryViewerView(LoginRequiredMixin, TemplateView):
    template_name = "core/story_viewer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        story_user = get_object_or_404(User.objects.select_related("profile"), username=self.kwargs.get("username"))
        stories = (
            Story.objects.active()
            .filter(user=story_user)
            .select_related("user", "user__profile")
            .prefetch_related("views__viewer")
        )
        for story in stories:
            if story.user_id != self.request.user.id:
                StoryView.objects.get_or_create(story=story, viewer=self.request.user)
        context["story_user"] = story_user
        context["stories"] = stories
        return context


@login_required
def story_delete(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if story.user_id != request.user.id:
        messages.error(request, "You can only delete your own stories.")
        return redirect("feed")
    if request.method == "POST":
        story.delete()
        messages.success(request, "Story deleted.")
    return redirect("feed")


@ratelimit(key="user_or_ip", rate="60/m", method="POST", block=True)
@login_required
def like_toggle(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "likes_count": post.likes.count()})
    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("feed"))


@ratelimit(key="user_or_ip", rate="30/m", method="POST", block=True)
@login_required
def comment_add(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment could not be empty.")
    return redirect("post_detail", pk=post.pk)


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user_id != request.user.id and comment.post.user_id != request.user.id:
        return HttpResponseForbidden("You cannot delete this comment.")
    post_pk = comment.post_id
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect("post_detail", pk=post_pk)


@ratelimit(key="user_or_ip", rate="30/m", method="POST", block=True)
@login_required
def follow_toggle(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user.id == request.user.id:
        messages.error(request, "You cannot follow yourself.")
        return redirect("profile_detail", username=username)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        follow.delete()
        messages.info(request, f"Unfollowed {target_user.username}.")
    else:
        messages.success(request, f"You are now following {target_user.username}.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"following": created, "followers_count": target_user.followers.count()})
    return redirect(request.POST.get("next") or reverse("profile_detail", kwargs={"username": username}))


class FollowListView(LoginRequiredMixin, TemplateView):
    template_name = "core/follow_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = get_object_or_404(User, username=self.kwargs.get("username"))
        mode = self.kwargs.get("mode")
        if mode == "followers":
            people = User.objects.filter(following__following=profile_user).select_related("profile")
        else:
            people = User.objects.filter(followers__follower=profile_user).select_related("profile")
        context.update({"profile_user": profile_user, "people": people, "mode": mode})
        return context


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "core/inbox.html"
    context_object_name = "conversations"

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .prefetch_related(
                "participants__profile",
                Prefetch("messages", queryset=Message.objects.select_related("sender").order_by("-timestamp")),
            )
            .order_by("-updated_at")
        )


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = "core/conversation_detail.html"
    context_object_name = "conversation"

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related("participants__profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages_qs = self.object.messages.select_related("sender", "sender__profile").order_by("-timestamp")[:50]
        Message.objects.filter(conversation=self.object, is_read=False).exclude(sender=self.request.user).update(
            is_read=True,
            read_at=timezone.now(),
        )
        context["chat_messages"] = reversed(list(messages_qs))
        context["message_form"] = MessageForm()
        context["other_user"] = self.object.get_other_participant(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.conversation = self.object
            message.save()
            Conversation.objects.filter(pk=self.object.pk).update(updated_at=timezone.now())
        return redirect("conversation_detail", pk=self.object.pk)


class NewConversationView(LoginRequiredMixin, TemplateView):
    template_name = "core/new_message.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = NewConversationForm()
        context["suggested_users"] = User.objects.exclude(pk=self.request.user.pk).select_related("profile")[:10]
        return context

    def post(self, request, *args, **kwargs):
        form = NewConversationForm(request.POST)
        if form.is_valid():
            target_user = form.cleaned_data["username"]
            if target_user == request.user:
                messages.error(request, "Choose someone else to message.")
                return redirect("new_message")
            conversation = Conversation.between(request.user, target_user)
            return redirect("conversation_detail", pk=conversation.pk)
        return render(request, self.template_name, {"form": form, "suggested_users": User.objects.none()})


@login_required
def older_messages(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    before_id = request.GET.get("before")
    qs = conversation.messages.select_related("sender").order_by("-timestamp")
    if before_id:
        qs = qs.filter(pk__lt=before_id)
    data = [
        {
            "id": message.pk,
            "sender": message.sender.username,
            "content": message.content,
            "image": message.image.url if message.image else "",
            "timestamp": message.timestamp.isoformat(),
            "is_read": message.is_read,
        }
        for message in qs[:30]
    ]
    return JsonResponse({"messages": data})
