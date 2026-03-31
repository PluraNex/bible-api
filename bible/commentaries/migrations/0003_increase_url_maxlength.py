"""Increase max_length of URLFields for Wikimedia Commons URLs."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commentaries", "0002_author_theological_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="author",
            name="portrait_image",
            field=models.URLField(blank=True, max_length=500, help_text="URL to author's portrait/icon"),
        ),
        migrations.AlterField(
            model_name="author",
            name="wikipedia_url",
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
