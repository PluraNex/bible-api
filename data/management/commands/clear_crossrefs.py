"""
Clear cross references to allow clean migration.

Usage:
    python manage.py clear_crossrefs
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Clear cross references for clean migration"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if cross_references table exists
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'cross_references'
                );
            """
            )

            if cursor.fetchone()[0]:
                self.stdout.write("Cross references table exists, clearing...")
                cursor.execute("TRUNCATE TABLE cross_references RESTART IDENTITY CASCADE;")
                self.stdout.write(self.style.SUCCESS("Successfully cleared cross references"))
            else:
                self.stdout.write("Cross references table does not exist")
