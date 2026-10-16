"""Measure a pipeline baseline against an isolated `_test` PostgreSQL database.

Generates the reference dataset in a subprocess (so peak RSS reflects the pipeline),
runs the real pipeline with phase timings and the warehouse lock hold time, then
exports a web snapshot to a temporary directory to measure its size. Never writes to
data/ or web/public. Linux-only peak RSS (resource.ru_maxrss in KiB).
"""

import argparse
import json
import platform
import resource
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import pipeline  # noqa: E402
from src.analytics.insights import read_analytics  # noqa: E402
from src.analytics.web_export import export_web_snapshot  # noqa: E402
from src.config.settings import Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402

PHASES = {
    "read_sources_with_hashes": "read_seconds",
    "validate_sources": "validate_seconds",
    "build_dimensions": "dimensions_seconds",
    "build_fact": "fact_seconds",
    "load_snapshot": "load_seconds",
    "reconcile_sql": "sql_reconciliation_seconds",
    "publish_snapshot": "publish_seconds",
}


def _directory_bytes(path: Path) -> dict[str, int]:
    files = [item for item in path.rglob("*") if item.is_file()]
    return {"files": len(files), "bytes": sum(item.stat().st_size for item in files)}


def measure(settings: Settings, orders: int, customers: int, products: int) -> dict:
    timings: dict[str, float] = {}

    def timed(name, function):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                timings[PHASES[name]] = round(time.perf_counter() - start, 3)

        return wrapper

    lease = pipeline.warehouse_lease

    @contextmanager
    def timed_lease(engine):
        start = time.perf_counter()
        try:
            with lease(engine) as connection:
                yield connection
        finally:
            timings["lock_held_seconds"] = round(time.perf_counter() - start, 3)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        settings = replace(settings, raw_path=root / "raw", processed_path=root / "processed")
        start = time.perf_counter()
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_mock_data.py",
                "--output",
                str(settings.raw_path),
                "--orders",
                str(orders),
                "--customers",
                str(customers),
                "--products",
                str(products),
            ],
            check=True,
            capture_output=True,
        )
        generation_seconds = round(time.perf_counter() - start, 3)
        for name in PHASES:
            setattr(pipeline, name, timed(name, getattr(pipeline, name)))
        pipeline.warehouse_lease = timed_lease
        start = time.perf_counter()
        report = pipeline.run(settings)
        total = round(time.perf_counter() - start, 3)
        peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        engine = engine_for(settings)
        try:
            with engine.connect() as connection:
                tables = read_analytics(connection)
            manifest = export_web_snapshot(tables, "baseline", root / "web")
        finally:
            engine.dispose()
        return {
            "dataset": {"seed": 42, "orders": orders, "customers": customers, "products": products},
            "environment": {"python": platform.python_version(), "machine": platform.machine()},
            "reconciliation_passed": report["passed"],
            "generation_seconds": generation_seconds,
            "pipeline_total_seconds": total,
            **dict(sorted(timings.items())),
            "peak_rss_mib": round(peak_rss_kib / 1024, 1),
            "raw_sources": _directory_bytes(settings.raw_path),
            "processed_exports": _directory_bytes(settings.processed_path),
            "web_snapshot": {
                **_directory_bytes(root / "web/snapshots" / manifest["snapshot"]),
                "contract_version": manifest["contract_version"],
            },
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=40000)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--products", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    settings = Settings.from_env()
    if not settings.database.endswith("_test"):
        raise SystemExit("Baseline runs only against an isolated *_test database")
    result = measure(settings, args.orders, args.customers, args.products)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
