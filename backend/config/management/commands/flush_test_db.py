"""Management command to flush test database tables."""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Flush test database tables while preserving schema"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get all tables except Django internal ones
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'django_%'
                AND tablename NOT LIKE 'auth_%'
                AND tablename NOT IN ('silk_request', 'silk_response', 'silk_sqlquery', 'silk_profile')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            if tables:
                self.stdout.write(f"Truncating {len(tables)} tables...")
                tables_str = ", ".join(tables)
                cursor.execute(f"TRUNCATE TABLE {tables_str} CASCADE")
                self.stdout.write(self.style.SUCCESS(f"Successfully truncated: {tables_str}"))
            else:
                self.stdout.write("No tables to truncate")

