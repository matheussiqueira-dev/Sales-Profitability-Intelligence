"""Revalidate the committed snapshot before exporting public aggregates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text  # noqa: E402

from src.analytics.insights import read_analytics  # noqa: E402
from src.analytics.web_export import export_web_snapshot  # noqa: E402
from src.config.settings import Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402
from src.database.loader import read_fact  # noqa: E402
from src.ingestion.csv_sources import read_sources  # noqa: E402
from src.validation.quality import validate_sources  # noqa: E402
from src.validation.reconciliation import reconcile, reconcile_sql  # noqa: E402

if __name__ == "__main__":
    settings = Settings.from_env()
    data, _ = validate_sources(read_sources(settings.raw_path))
    engine = engine_for(settings)
    try:
        with engine.connect() as connection:
            report = reconcile_sql(connection, reconcile(data, read_fact(connection)))
            if not report["passed"]:
                raise ValueError("Do not export a divergent snapshot")
            metadata = connection.execute(
                text("SELECT contract_version,completed_at FROM analytics.pipeline_metadata")
            ).one()
            if metadata[0] != 2 or metadata[1] is None:
                raise ValueError("No committed V2 snapshot")
            print(export_web_snapshot(read_analytics(connection), metadata[1]))
    finally:
        engine.dispose()
