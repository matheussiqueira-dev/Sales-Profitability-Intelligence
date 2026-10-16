"""Recoverable publication: database and filesystem have separate commits.

The completion marker is published last. Individual files are atomic; the whole
CSV bundle is not. Consumers must check the marker and hashes before refresh.
"""

import argparse
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from src.analytics.insights import generate_insights, read_analytics
from src.analytics.web_export import export_web_snapshot
from src.config.settings import ROOT, Settings
from src.database.connection import engine_for
from src.database.lease import warehouse_lease
from src.database.loader import DIMENSIONS, OWNER, read_fact
from src.validation.quality import validate_sources
from src.validation.reconciliation import reconcile, reconcile_sql
from src.validation.schemas import CONTRACTS


class PublicationError(RuntimeError):
    """Warehouse is committed; retry publication without rerunning ingestion."""


@contextmanager
def atomic_output(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        yield temporary
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def save_json(path: Path, value):
    with atomic_output(path) as temporary:
        temporary.write_text(
            json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )


def publish_snapshot(settings, dimensions, fact, tables, report, completed_at):
    """Caller holds the warehouse lease and has already committed reconciliation."""
    if not report.get("passed") or completed_at is None:
        raise ValueError("Only reconciled, committed snapshots may be published")
    try:
        save_json(
            settings.processed_path / "publication.json",
            {"status": "publishing", "warehouse_completed_at": str(completed_at)},
        )
        insights = generate_insights(tables)
        save_json(settings.processed_path / "insights.json", insights)
        hashes = {}
        for name, frame in {**dimensions, "fact_sales": fact, **tables}.items():
            path = settings.processed_path / f"{name}.csv"
            with atomic_output(path) as temporary:
                frame.to_csv(temporary, index=False)
                hashes[path.name] = hashlib.sha256(temporary.read_bytes()).hexdigest()
        save_json(settings.processed_path / "reconciliation.json", report)
        web_manifest = None
        if not settings.database.endswith("_test"):
            web_manifest = export_web_snapshot(tables, completed_at)
        publication = {
            "status": "published",
            "warehouse_completed_at": str(completed_at),
            "sha256": hashes,
            "web_snapshot": web_manifest["snapshot"] if web_manifest else None,
            "alerts_count": insights["alerts_count"],
        }
        save_json(settings.processed_path / "publication.json", publication)
        return publication
    except Exception as exc:
        raise PublicationError(
            "Warehouse committed; export publication failed. Repair the destination and run "
            "python -m src.analytics.publication to retry without reloading sources."
        ) from exc


def republish(settings):
    """Recover from persisted raw sources, regardless of current CSV files on disk."""
    engine = engine_for(settings)
    try:
        with warehouse_lease(engine) as connection:
            connection.execution_options(isolation_level="REPEATABLE READ")
            with connection.begin():
                connection.execute(text("SET TRANSACTION READ ONLY"))
                metadata = connection.execute(
                    text(
                        "SELECT owner,contract_version,completed_at "
                        "FROM analytics.pipeline_metadata WHERE singleton"
                    )
                ).one_or_none()
                if (
                    metadata is None
                    or metadata[0] != OWNER
                    or metadata[1] != 2
                    or metadata[2] is None
                ):
                    raise ValueError("No committed, owned V2 snapshot to publish")
                original = {
                    name: pd.read_sql(
                        text(f'SELECT * FROM raw."{name}"'), connection, coerce_float=False
                    )
                    for name in CONTRACTS
                }
                cleaned, _ = validate_sources(original)
                fact = read_fact(connection)
                report = reconcile_sql(connection, reconcile(cleaned, fact))
                if not report["passed"]:
                    raise ValueError("Do not publish a divergent snapshot")
                dimensions = {
                    name: pd.read_sql(
                        text(f'SELECT * FROM analytics."{name}" ORDER BY 1'),
                        connection,
                        coerce_float=False,
                    )
                    for name in DIMENSIONS
                }
                tables = read_analytics(connection)
            return publish_snapshot(settings, dimensions, fact, tables, report, metadata[2])
    finally:
        engine.dispose()


def verify_publication(path: Path):
    """Preflight for CSV consumers; not a lock around their subsequent refresh."""
    marker_path = path / "publication.json"
    marker_bytes = marker_path.read_bytes()
    marker = json.loads(marker_bytes)
    hashes = marker.get("sha256")
    required = {f"{name}.csv" for name in [*DIMENSIONS, "fact_sales"]}
    if (
        marker.get("status") != "published"
        or not isinstance(hashes, dict)
        or not required.issubset(hashes)
    ):
        raise ValueError("Publication is incomplete; run recovery before refreshing CSVs")
    for name, expected in hashes.items():
        if Path(name).name != name or not name.endswith(".csv"):
            raise ValueError("Invalid publication file name")
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Publication hash mismatch: {name}")
    if marker_path.read_bytes() != marker_bytes:
        raise ValueError("Publication changed during verification; retry")
    return marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify", action="store_true", help="Verify CSV hashes without a database"
    )
    args = parser.parse_args()
    try:
        if args.verify:
            # Verification does not need a database password or driver.
            load_dotenv(ROOT / ".env", override=False)
            publication = verify_publication(
                ROOT / os.getenv("DATA_PROCESSED_PATH", "data/processed")
            )
        else:
            publication = republish(Settings.from_env())
    except Exception as exc:
        raise SystemExit(f"Publication failed ({type(exc).__name__})") from None
    print(json.dumps(publication, indent=2))


if __name__ == "__main__":
    main()
