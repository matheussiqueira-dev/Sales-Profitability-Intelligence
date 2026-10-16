import json
import os
from dataclasses import replace

import pytest
from sqlalchemy import text

from scripts.generate_mock_data import generate, write_dataset
from src import pipeline
from src.analytics.publication import PublicationError, republish
from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.lease import warehouse_lease
from src.pipeline import run


@pytest.mark.integration
def test_committed_warehouse_recovers_exports_without_disk_sources(tmp_path, monkeypatch):
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Isolated PostgreSQL required")
    settings = Settings.from_env()
    assert settings.database.endswith("_test")
    settings = replace(settings, raw_path=tmp_path / "raw", processed_path=tmp_path / "processed")
    write_dataset(generate(42, 20, 10, 10), settings.raw_path)
    publisher = pipeline.publish_snapshot

    def fail_after_commit(*args):
        raise PublicationError("forced post-commit failure")

    monkeypatch.setattr("src.pipeline.publish_snapshot", fail_after_commit)
    with pytest.raises(PublicationError):
        run(settings)
    engine = engine_for(settings)
    try:
        with engine.connect() as connection:
            before = connection.execute(
                text("SELECT completed_at FROM analytics.pipeline_metadata")
            ).scalar_one()
            count = connection.execute(
                text("SELECT count(*) FROM analytics.fact_sales")
            ).scalar_one()
        assert before is not None and count > 0
        for path in settings.raw_path.glob("*.csv"):
            path.unlink()
        monkeypatch.setattr("src.pipeline.publish_snapshot", publisher)
        publication = republish(settings)
        assert publication["status"] == "published"
        with engine.connect() as connection:
            after = connection.execute(
                text("SELECT completed_at FROM analytics.pipeline_metadata")
            ).scalar_one()
            assert after == before
        assert json.loads((settings.processed_path / "reconciliation.json").read_text())["passed"]
        # Session lock must remain held after commit and be released after failure.
        with pytest.raises(ValueError, match="forced"):
            with warehouse_lease(engine) as connection:
                with connection.begin():
                    connection.execute(text("SELECT 1"))
                with pytest.raises(RuntimeError, match="Another pipeline"):
                    republish(settings)
                raise ValueError("forced")
        with warehouse_lease(engine):
            pass
    finally:
        engine.dispose()
