"""Run a validated atomic full-refresh snapshot from CSV to PostgreSQL."""

import argparse
import hashlib
import json
import logging
from pathlib import Path

from sqlalchemy import text

from src.analytics.insights import generate_insights, read_analytics
from src.config.settings import Settings
from src.database.connection import engine_for
from src.database.loader import initialize, load_snapshot, read_fact
from src.ingestion.csv_sources import read_sources
from src.transformation.dimensions import build_dimensions
from src.transformation.sales import build_fact
from src.validation.quality import QualityError, validate_sources
from src.validation.reconciliation import reconcile, reconcile_sql

LOG = logging.getLogger(__name__)


def save_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    temporary.replace(path)


def run(settings, validate_only=False):
    LOG.info("Pipeline started")
    original = read_sources(settings.raw_path)
    try:
        cleaned, quality = validate_sources(original)
    except QualityError as exc:
        save_json(settings.processed_path / "quality-report.json", exc.report)
        raise
    quality["source_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(settings.raw_path.glob("*.csv"))
    }
    save_json(settings.processed_path / "quality-report.json", quality)
    LOG.info("Source quality passed")
    if validate_only:
        return quality
    dimensions = build_dimensions(cleaned)
    fact = build_fact(cleaned)
    LOG.info("Built %s non-cancelled sale items", len(fact))
    engine = engine_for(settings)
    try:
        with engine.begin() as connection:
            locked = connection.execute(
                text("SELECT pg_try_advisory_xact_lock(831024915)")
            ).scalar_one()
            if not locked:
                raise RuntimeError("Another pipeline is loading this database")
            initialize(connection)
            LOG.info("Loading owned raw, staging and analytics tables atomically")
            load_snapshot(connection, original, cleaned, dimensions, fact)
            persisted = read_fact(connection)
            report = reconcile_sql(connection, reconcile(cleaned, persisted))
            save_json(settings.processed_path / "reconciliation.json", report)
            if not report["passed"]:
                raise ValueError("Financial reconciliation failed; transaction rolled back")
            tables = read_analytics(connection)
            insights = generate_insights(tables)
            connection.execute(
                text("UPDATE analytics.pipeline_metadata SET completed_at = current_timestamp")
            )
        # Publish successful exports only after PostgreSQL has committed.
        save_json(settings.processed_path / "insights.json", insights)
        for name, frame in {**dimensions, "fact_sales": persisted, **tables}.items():
            frame.to_csv(settings.processed_path / f"{name}.csv", index=False)
        LOG.info("Reconciliation passed for all metrics, rows and order freight")
        LOG.info(
            "%s deterministic rules evaluated; %s alerts",
            len(insights["rules_evaluated"]),
            insights["alerts_count"],
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
    except Exception as exc:
        # Avoid DSNs/SQL parameters in terminal logs; quality details live in report.
        LOG.error(
            "Pipeline failed (%s). Database changes were not accepted; inspect reports.",
            type(exc).__name__,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
