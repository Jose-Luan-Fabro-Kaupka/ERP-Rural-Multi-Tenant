import os
import sys

import psycopg2
from django.core.management.base import BaseCommand
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def _valid_db_identifier(name: str) -> bool:
    if not name or len(name) > 63:
        return False
    return all(c.isalnum() or c == "_" for c in name)


class Command(BaseCommand):
    help = (
        "Creates the PostgreSQL database named DB_NAME if it does not exist. "
        "Connects using DB_* to the maintenance database (DB_MAINTENANCE_NAME, default postgres)."
    )

    def handle(self, *args, **options):
        db_name = os.environ.get("DB_NAME", "agrodb")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        maintenance_db = os.environ.get("DB_MAINTENANCE_NAME", "postgres")

        if not _valid_db_identifier(db_name):
            self.stderr.write(
                "DB_NAME must be non-empty, at most 63 chars, and use only letters, digits and underscores."
            )
            sys.exit(1)

        try:
            conn = psycopg2.connect(
                dbname=maintenance_db,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                connect_timeout=60,
            )
        except psycopg2.OperationalError as e:
            self.stderr.write(
                f"Could not connect to PostgreSQL (database={maintenance_db!r}, host={db_host}): {e}"
            )
            sys.exit(1)

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (db_name,),
                )
                if cur.fetchone():
                    self.stdout.write(f"Database {db_name!r} already exists.")
                    return
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                )
                self.stdout.write(self.style.SUCCESS(f"Created database {db_name!r}."))
        finally:
            conn.close()
