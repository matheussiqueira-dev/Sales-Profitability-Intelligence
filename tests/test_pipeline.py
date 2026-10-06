import os
from dataclasses import replace

import pytest
from sqlalchemy import text

from scripts.generate_mock_data import generate, write_dataset
from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.loader import initialize, read_statements
from src.pipeline import run


@pytest.mark.integration
def test_postgres_repeatable_load_and_rollback(tmp_path, monkeypatch):
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 and POSTGRES_DB ending in _test")
    settings = Settings.from_env()
    if not settings.database.endswith("_test"):
        pytest.fail("Integration tests require isolated database ending in _test")
    settings = replace(settings, raw_path=tmp_path / "raw", processed_path=tmp_path / "processed")
    write_dataset(generate(42, 80, 20, 20), settings.raw_path)
    assert run(settings)["passed"]
    engine = engine_for(settings)
    try:
        with engine.connect() as connection:
            before = connection.execute(
                text("SELECT count(*),sum(net_revenue) FROM analytics.fact_sales")
            ).one()
        assert run(settings)["passed"]
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*),sum(net_revenue) FROM analytics.fact_sales")
                ).one()
                == before
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM analytics.vw_target_performance")
                ).scalar_one()
                == 96
            )
            for statement in read_statements("07_example_queries.sql"):
                assert connection.execute(text(statement)).returns_rows
        # Unknown warehouse tables must stop refresh without touching their content.
        with engine.begin() as connection:
            savepoint = connection.begin_nested()
            connection.execute(text("CREATE TABLE staging.foreign_table(value text)"))
            connection.execute(text("INSERT INTO staging.foreign_table VALUES ('preserve')"))
            with pytest.raises(ValueError, match="Unexpected tables"):
                initialize(connection)
            assert (
                connection.execute(text("SELECT value FROM staging.foreign_table")).scalar_one()
                == "preserve"
            )
            savepoint.rollback()
        # Force a failure after insertion, verify previous committed snapshot survives.
        monkeypatch.setattr(
            "src.pipeline.reconcile_sql", lambda connection, report: {"passed": False}
        )
        write_dataset(generate(43, 40, 20, 20), settings.raw_path)
        with pytest.raises(ValueError, match="rolled back"):
            run(settings)
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*),sum(net_revenue) FROM analytics.fact_sales")
                ).one()
                == before
            )
    finally:
        engine.dispose()
