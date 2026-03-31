"""Add person OneToOneField to Author — link to unified Person hub."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("commentaries", "0003_increase_url_maxlength"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="person",
            field=models.OneToOneField(
                blank=True,
                help_text="Link to unified Person identity hub",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="author_profile",
                to="people.person",
            ),
        ),
    ]
