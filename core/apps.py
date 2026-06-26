def ready(self):
    import core.signals  # noqa: F401

    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not User.objects.filter(username="potling").exists():
            User.objects.create_superuser(
                username="potling",
                email="your@email.com",
                password="Potling123!"
            )
    except Exception:
        pass