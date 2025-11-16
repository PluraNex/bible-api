"""
Enable pgvector extension for the database.
This is required for vector similarity search operations.
"""
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = []  # No dependencies, runs first

    operations = [
        CreateExtension('vector'),
    ]
