from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # required for CREATE INDEX CONCURRENTLY

    dependencies = [
        ("bible", "0011_create_verse_embeddings"),
    ]

    operations = [
        # Placeholder migration: vector dims + indexes will be handled separately per environment capacity.
        migrations.RunSQL(sql="SELECT 1", reverse_sql="SELECT 1"),
    ]
