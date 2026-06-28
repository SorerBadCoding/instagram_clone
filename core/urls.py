"""URL routes for the Instagram clone."""

from django.urls import path

from . import views


urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("", views.FeedView.as_view(), name="feed"),
    path("explore/", views.ExploreView.as_view(), name="explore"),
    path("inbox/", views.InboxView.as_view(), name="inbox"),
    path("inbox/new/", views.NewConversationView.as_view(), name="new_message"),
    path("inbox/<int:pk>/", views.ConversationDetailView.as_view(), name="conversation_detail"),
    path("inbox/<int:pk>/older/", views.older_messages, name="older_messages"),
    path("post/new/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<int:pk>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<int:pk>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("post/<int:pk>/like/", views.like_toggle, name="like_toggle"),
    path("post/<int:pk>/comment/", views.comment_add, name="comment_add"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/<str:username>/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("profile/<str:username>/<str:mode>/", views.FollowListView.as_view(), name="follow_list"),
    path("follow/<str:username>/", views.follow_toggle, name="follow_toggle"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("story/new/", views.StoryCreateView.as_view(), name="story_create"),
    path("story/<int:pk>/delete/", views.story_delete, name="story_delete"),
    path("story/<str:username>/", views.StoryViewerView.as_view(), name="story_viewer"),
]
