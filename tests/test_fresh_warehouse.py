import os
from dataclasses import replace

import pytest
from sqlalchemy import inspect, text

from scripts.generate_mock_data import generate, write_dataset
from src.config.settings import Settings
from src.database.connection import engine_for
from src.pipeline import run


@pytest.mark.integration
def test_fresh_database_from_versioned_ddl(tmp_path):
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Isolated PostgreSQL required")
    import psycopg
    from psycopg import sql

    settings = Settings.from_env()
    assert settings.database.endswith("_test")
    name = "sales_profitability_fresh_test"
    with psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname="postgres",
        user=settings.user,
        password=settings.password,
        autocommit=True,
    ) as admin:
        exists = admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone()
        if not exists:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    settings = replace(
        settings, database=name, raw_path=tmp_path / "raw", processed_path=tmp_path / "processed"
    )
    write_dataset(generate(42, 80, 20, 20), settings.raw_path)
    assert run(settings)["passed"]
    engine = engine_for(settings)
    try:
        with engine.connect() as connection:
            metadata = inspect(connection)
            assert len(metadata.get_foreign_keys("fact_sales", schema="analytics")) == 5
            assert metadata.get_pk_constraint("variable_costs", schema="staging")[
                "constrained_columns"
            ] == ["order_item_id"]
            assert (
                connection.execute(
                    text("SELECT version FROM analytics.schema_migrations")
                ).scalar_one()
                == 2
            )
            assert (
                connection.execute(
                    text("SELECT analytics.discount_limit(100,.1,70,.15)")
                ).scalar_one()
                > 0
            )
    finally:
        engine.dispose()
