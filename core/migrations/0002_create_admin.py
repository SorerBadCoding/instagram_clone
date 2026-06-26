from django.db import migrations

def create_admin(apps, schema_editor):
    User = apps.get_model("auth", "User")

    if not User.objects.filter(username="potling").exists():
        User.objects.create_superuser(
            username="potling",
            email="Sor.er2013@email.com",
            password="Potling123!"
        )

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]