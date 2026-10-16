"""Inspect the committed snapshot and execute demonstration queries, read-only."""

import json
import sys
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analytics.insights import read_analytics  # noqa: E402
from src.analytics.publication import save_json  # noqa: E402
from src.config.settings import Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402
from src.database.loader import read_statements  # noqa: E402


def verify(settings):
    engine = engine_for(settings)
    try:
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            inspector = inspect(connection)
            counts = {}
            for schema in ("raw", "staging", "analytics"):
                for name in inspector.get_table_names(schema=schema):
                    # Names originate from PostgreSQL metadata and are safely quoted.
                    table = connection.dialect.identifier_preparer.quote_identifier(name)
                    counts[f"{schema}.{name}"] = connection.execute(
                        text(f"SELECT count(*) FROM {schema}.{table}")
                    ).scalar_one()
            summary = read_analytics(connection)["sales_summary"].to_dict("records")[0]
            examples = []
            for statement in read_statements("07_example_queries.sql"):
                if statement.strip():
                    result = connection.execute(text(statement))
                    if result.returns_rows:
                        examples.append(len(result.all()))
            metadata = dict(
                connection.execute(text("SELECT * FROM analytics.pipeline_metadata"))
                .mappings()
                .one()
            )
        report = {
            "counts": counts,
            "summary": summary,
            "example_query_rows": examples,
            "metadata": metadata,
        }
        save_json(settings.processed_path / "database-verification.json", report)
        return report
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps(verify(Settings.from_env()), indent=2, ensure_ascii=False, default=str))
