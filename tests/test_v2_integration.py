import os
from dataclasses import replace

import pytest
from sqlalchemy import inspect, text

from scripts.generate_mock_data import generate, write_dataset
from src.analytics.insights import read_analytics
from src.analytics.web_export import export_web_snapshot
from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.loader import initialize
from src.pipeline import run


@pytest.fixture
def db():
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Isolated PostgreSQL required")
    settings = Settings.from_env()
    assert settings.database.endswith("_test")
    engine = engine_for(settings)
    try:
        yield settings, engine
    finally:
        engine.dispose()


@pytest.mark.integration
def test_upgrade_preserves_legacy_rows_and_totals(db):
    _, engine = db
    # Represent a populated V1 schema in a rollback-only transaction on isolated test DB.
    with engine.begin() as connection:
        checkpoint = connection.begin_nested()
        inspector = inspect(connection)
        for name in inspector.get_view_names(schema="analytics"):
            quoted = connection.dialect.identifier_preparer.quote_identifier(name)
            connection.execute(text(f"DROP VIEW analytics.{quoted}"))
        for constraint in inspector.get_check_constraints("fact_sales", schema="analytics"):
            if "variable_cost" in constraint["sqltext"]:
                quoted = connection.dialect.identifier_preparer.quote_identifier(constraint["name"])
                connection.execute(
                    text(f"ALTER TABLE analytics.fact_sales DROP CONSTRAINT {quoted}")
                )
        connection.execute(
            text(
                "ALTER TABLE analytics.fact_sales DROP COLUMN variable_cost_rate, "
                "DROP COLUMN variable_cost_fixed,DROP COLUMN variable_cost_value"
            )
        )
        connection.execute(
            text(
                "UPDATE analytics.fact_sales SET contribution_margin="
                "net_revenue-total_product_cost-freight_allocated"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE analytics.fact_sales ADD CONSTRAINT fact_sales_check2 "
                "CHECK(contribution_margin=net_revenue-total_product_cost-freight_allocated)"
            )
        )
        connection.execute(text("UPDATE analytics.pipeline_metadata SET contract_version=1"))
        connection.execute(text("DROP TABLE analytics.schema_migrations"))
        before = connection.execute(
            text("SELECT count(*),sum(contribution_margin) FROM analytics.fact_sales")
        ).one()
        initialize(connection)
        assert (
            connection.execute(text("SELECT analytics.discount_limit(100,.20,70,.80)")).scalar_one()
            is None
        )
        assert (
            connection.execute(
                text("SELECT count(*),sum(contribution_margin) FROM analytics.fact_sales")
            ).one()
            == before
        )
        assert (
            connection.execute(
                text("SELECT contract_version FROM analytics.pipeline_metadata")
            ).scalar_one()
            == 2
        )
        assert (
            connection.execute(
                text("SELECT sum(variable_cost_value) FROM analytics.fact_sales")
            ).scalar_one()
            == 0
        )
        checkpoint.rollback()


@pytest.mark.integration
def test_lock_rejects_second_loader_and_export_hashes(db, tmp_path):
    settings, engine = db
    settings = replace(settings, raw_path=tmp_path / "raw", processed_path=tmp_path / "processed")
    write_dataset(generate(42, 20, 10, 10), settings.raw_path)
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(831024915)"))
        with pytest.raises(RuntimeError, match="Another pipeline"):
            run(settings)
    with engine.connect() as connection:
        manifest = export_web_snapshot(read_analytics(connection), "2026-10-06", tmp_path / "web")
    import hashlib

    for name, checksum in manifest["sha256"].items():
        path = tmp_path / "web/snapshots" / manifest["snapshot"] / f"{name}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum
    assert manifest["contract_version"] == 2
    assert manifest["reconciled"]
