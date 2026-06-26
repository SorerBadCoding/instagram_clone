from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Instagram Clone Core"

    def ready(self):
        import core.signals  # noqa: F401

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            if not User.objects.filter(username="potling").exists():
                User.objects.create_superuser(
                    username="potling",
                    email="Sor.er2013@email.com",
                    password="Potling123!"
                )
        except Exception as e:
            print("ADMIN CREATE ERROR:", e)