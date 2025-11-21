"""
Custom test runner to handle PostgreSQL test database cleanup.

This runner ensures that orphaned database connections are terminated before
creating test databases, which is especially important when using Neon or
other serverless PostgreSQL instances.
"""

import os
import sys
from typing import Any

from django.conf import settings
from django.db import connections
from django.test.runner import DiscoverRunner


class PostgresTestRunner(DiscoverRunner):
    """Custom test runner that handles PostgreSQL connection cleanup."""

    def setup_databases(self, **kwargs: Any) -> list[tuple[Any, str, bool]]:
        """Override to forcefully terminate connections before creating test DB."""
        # Warn if TEST_DATABASE_URL is not set
        test_db_url = os.getenv("TEST_DATABASE_URL")
        if not test_db_url:
            self.log(
                "=" * 70,
                level=2,
            )
            self.log(
                "WARNING: TEST_DATABASE_URL environment variable is not set!",
                level=2,
            )
            self.log(
                "Tests may run against your production database configuration.",
                level=2,
            )
            self.log(
                "Please set TEST_DATABASE_URL to a local PostgreSQL instance:",
                level=2,
            )
            self.log(
                "  export TEST_DATABASE_URL=postgres://localhost:5432/standardstitch_test",
                level=2,
            )
            self.log(
                "=" * 70,
                level=2,
            )

        # Terminate all connections to potential test databases before setup
        for alias in connections:
            connection = connections[alias]
            if connection.vendor == "postgresql":
                test_config = connection.settings_dict.get("TEST", {})
                test_db_name = test_config.get("NAME")

                if not test_db_name:
                    # Generate default test database name
                    db_name = connection.settings_dict.get("NAME", "")
                    test_db_name = f"test_{db_name}"

                # Kill all connections to the test database
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT pg_terminate_backend(pg_stat_activity.pid)
                            FROM pg_stat_activity
                            WHERE pg_stat_activity.datname = %s
                              AND pid <> pg_backend_pid();
                            """,
                            [test_db_name],
                        )
                        terminated = cursor.fetchall()
                        count = sum(1 for row in terminated if row[0])
                        if count > 0:
                            self.log(
                                f"Terminated {count} connection(s) to {test_db_name}",
                                level=1,
                            )
                except Exception:
                    # Ignore errors if database doesn't exist yet
                    pass

        return super().setup_databases(**kwargs)

    def log(self, msg: str, level: int = 1) -> None:
        """Log a message if verbosity level is sufficient."""
        if self.verbosity >= level:
            print(msg, file=sys.stderr)


