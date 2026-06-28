"""Forms used across the Instagram Clone app."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Comment, Message, Post, Profile, Story


BOOTSTRAP_TEXT = {"class": "form-control"}
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
MAX_STORY_VIDEO_SIZE = 25 * 1024 * 1024


def validate_upload(file, allowed_types, max_size):
    if not file:
        return
    content_type = getattr(file, "content_type", "")
    if content_type and content_type not in allowed_types:
        raise forms.ValidationError("Unsupported file type.")
    if file.size > max_size:
        raise forms.ValidationError("File is too large.")


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Username"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirm password"})
        for field in self.fields.values():
            field.help_text = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs=BOOTSTRAP_TEXT))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs=BOOTSTRAP_TEXT))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs=BOOTSTRAP_TEXT))

    class Meta:
        model = Profile
        fields = [
            "profile_picture",
            "bio",
            "website",
            "location",
            "show_activity_status",
            "allow_story_replies",
        ]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Tell people about yourself"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Location"}),
            "show_activity_status": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "allow_story_replies": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user_id:
            user = self.instance.user
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        validate_upload(picture, IMAGE_TYPES, MAX_UPLOAD_SIZE)
        return picture

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            profile.save()
        return profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["image", "caption", "location"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Write a caption..."}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Add location"}),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        validate_upload(image, IMAGE_TYPES, MAX_UPLOAD_SIZE)
        return image


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Add a comment...", "autocomplete": "off"}
            )
        }


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["image", "video", "caption", "privacy"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "video": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.TextInput(attrs={"class": "form-control", "placeholder": "Add a caption (optional)"}),
            "privacy": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get("image")
        video = cleaned.get("video")
        if not image and not video:
            raise forms.ValidationError("Upload an image or a video story.")
        if image and video:
            raise forms.ValidationError("Choose either an image or a video, not both.")
        validate_upload(image, IMAGE_TYPES, MAX_UPLOAD_SIZE)
        validate_upload(video, VIDEO_TYPES, MAX_STORY_VIDEO_SIZE)
        return cleaned


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content", "image"]
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Message...",
                    "autocomplete": "off",
                    "data-message-input": "true",
                }
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control form-control-sm"}),
        }

    def clean(self):
        cleaned = super().clean()
        content = cleaned.get("content", "").strip()
        image = cleaned.get("image")
        if not content and not image:
            raise forms.ValidationError("Send a message or an image.")
        validate_upload(image, IMAGE_TYPES, MAX_UPLOAD_SIZE)
        return cleaned


class NewConversationForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control search-input",
                "placeholder": "Search username",
                "autocomplete": "off",
            }
        )
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        try:
            return User.objects.get(username__iexact=username)
        except User.DoesNotExist as exc:
            raise forms.ValidationError("No user with that username exists.") from exc
