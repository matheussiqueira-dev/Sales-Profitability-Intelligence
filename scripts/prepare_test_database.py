"""Create an isolated test database if absent; do not drop any database."""

import sys
from pathlib import Path

import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import Settings  # noqa: E402


def main():
    settings = Settings.from_env()
    name = "sales_profitability_test"
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname="postgres",
        user=settings.user,
        password=settings.password,
        autocommit=True,
        connect_timeout=10,
    ) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", (name,)
        ).fetchone()
        if not exists:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


if __name__ == "__main__":
    main()
