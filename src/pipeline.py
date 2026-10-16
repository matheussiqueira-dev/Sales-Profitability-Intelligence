"""Run a validated atomic full-refresh snapshot from CSV to PostgreSQL."""

import argparse
import logging

from sqlalchemy import text

from src.analytics.insights import read_analytics
from src.analytics.publication import PublicationError, publish_snapshot, save_json
from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.lease import warehouse_lease
from src.database.loader import initialize, load_snapshot, read_fact
from src.ingestion.csv_sources import read_sources_with_hashes
from src.transformation.dimensions import build_dimensions
from src.transformation.sales import build_fact
from src.validation.quality import QualityError, validate_sources
from src.validation.reconciliation import reconcile, reconcile_sql

LOG = logging.getLogger(__name__)


def run(settings, validate_only=False):
    LOG.info("Pipeline started")
    original, source_hashes = read_sources_with_hashes(settings.raw_path)
    try:
        cleaned, quality = validate_sources(original)
    except QualityError as exc:
        exc.report["source_sha256"] = source_hashes
        save_json(settings.processed_path / "quality-report.json", exc.report)
        raise
    quality["source_sha256"] = source_hashes
    save_json(settings.processed_path / "quality-report.json", quality)
    LOG.info("Source quality passed")
    if validate_only:
        return quality
    dimensions = build_dimensions(cleaned)
    fact = build_fact(cleaned)
    LOG.info("Built %s non-cancelled sale items", len(fact))
    engine = engine_for(settings)
    try:
        with warehouse_lease(engine) as connection:
            with connection.begin():
                initialize(connection)
                LOG.info("Loading owned raw, staging and analytics tables atomically")
                load_snapshot(connection, original, cleaned, dimensions, fact)
                persisted = read_fact(connection)
                report = reconcile_sql(connection, reconcile(cleaned, persisted))
                save_json(settings.processed_path / "reconciliation.json", report)
                if not report["passed"]:
                    raise ValueError("Financial reconciliation failed; transaction rolled back")
                tables = read_analytics(connection)
                connection.execute(
                    text("UPDATE analytics.pipeline_metadata SET completed_at = clock_timestamp()")
                )
                completed_at = connection.execute(
                    text("SELECT completed_at FROM analytics.pipeline_metadata")
                ).scalar_one()
            publication = publish_snapshot(
                settings, dimensions, persisted, tables, report, completed_at
            )
        LOG.info("Reconciliation passed for all metrics, rows and order freight")
        LOG.info(
            "%s deterministic alerts published",
            publication["alerts_count"],
        )
        LOG.info("Pipeline completed successfully")
        return report
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    try:
        run(Settings.from_env(), args.validate_only)
    except PublicationError as exc:
        LOG.error("%s", exc)
        raise SystemExit(2) from None
    except Exception as exc:
        # Avoid DSNs/SQL parameters in terminal logs; quality details live in report.
        LOG.error(
            "Pipeline failed (%s). Inspect reports and pipeline_metadata before retrying.",
            type(exc).__name__,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
