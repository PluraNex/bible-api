"""Add person OneToOneField to CanonicalEntity — link to unified Person hub."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("entities", "0001_entities_and_symbols"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="canonicalentity",
            name="person",
            field=models.OneToOneField(
                blank=True,
                help_text="Link to unified Person identity hub (PERSON/DEITY namespace only)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="biblical_profile",
                to="people.person",
            ),
        ),
    ]
