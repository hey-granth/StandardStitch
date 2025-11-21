"""
Management command to forcibly terminate all connections to test databases.

This is useful when test databases are accidentally created on Neon or other
cloud Postgres instances where connection pooling can cause locks.

Usage:
    python manage.py kill_test_db_sessions
    python manage.py kill_test_db_sessions --database=test_neondb
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connections


class Command(BaseCommand):
    help = "Forcibly terminate all connections to test databases"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--database",
            type=str,
            default=None,
            help="Specific test database name to target (e.g., test_neondb)",
        )
        parser.add_argument(
            "--alias",
            type=str,
            default="default",
            help="Database alias to use from Django settings (default: 'default')",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        alias: str = options["alias"]
        target_db_name: str | None = options["database"]

        if alias not in connections:
            self.stderr.write(
                self.style.ERROR(f"Database alias '{alias}' not found in settings")
            )
            return

        db_connection = connections[alias]

        # Determine target database name
        if target_db_name is None:
            # Use configured test database name
            test_config = db_connection.settings_dict.get("TEST", {})
            target_db_name = test_config.get("NAME")

            if not target_db_name:
                # Generate default test database name
                db_name = db_connection.settings_dict.get("NAME", "")
                target_db_name = f"test_{db_name}"

        self.stdout.write(
            f"Terminating connections to test database: {target_db_name}"
        )

        # Check if we're using PostgreSQL
        if db_connection.vendor != "postgresql":
            self.stderr.write(
                self.style.ERROR(
                    f"This command only supports PostgreSQL. "
                    f"Current database vendor: {db_connection.vendor}"
                )
            )
            return

        try:
            with db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s
                      AND pid <> pg_backend_pid();
                    """,
                    [target_db_name],
                )
                result = cursor.fetchall()
                terminated_count = sum(1 for row in result if row[0])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully terminated {terminated_count} connection(s) "
                    f"to database '{target_db_name}'"
                )
            )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error terminating connections: {str(e)}")
            )
            raise

