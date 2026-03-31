"""Create Person model — unified identity hub."""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_name", models.CharField(help_text="Primary display name", max_length=200)),
                ("slug", models.SlugField(help_text="URL-safe identifier", max_length=120, unique=True)),
                ("person_type", models.CharField(
                    choices=[
                        ("biblical", "Biblical Figure"),
                        ("historical", "Historical Figure"),
                        ("author", "Commentary Author"),
                        ("mixed", "Biblical + Historical Author"),
                    ],
                    help_text="Primary classification",
                    max_length=20,
                )),
                ("birth_year", models.CharField(blank=True, help_text="Birth year, approximate allowed", max_length=50)),
                ("death_year", models.CharField(blank=True, help_text="Death year, approximate allowed", max_length=50)),
                ("description", models.TextField(blank=True, help_text="Brief description")),
                ("wikipedia_url", models.URLField(blank=True, max_length=500)),
                ("portrait_image", models.URLField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "people_person",
                "ordering": ["canonical_name"],
                "verbose_name": "Person",
                "verbose_name_plural": "People",
            },
        ),
        migrations.AddIndex(
            model_name="person",
            index=models.Index(fields=["person_type"], name="people_type_idx"),
        ),
        migrations.AddIndex(
            model_name="person",
            index=models.Index(fields=["slug"], name="people_slug_idx"),
        ),
    ]
