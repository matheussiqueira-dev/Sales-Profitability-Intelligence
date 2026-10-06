from pathlib import Path

import pandas as pd
from sqlalchemy import MetaData, Table, inspect, text

from src.validation.schemas import CONTRACTS

SQL_PATH = Path(__file__).resolve().parents[2] / "sql"
OWNER = "sales-profitability-intelligence"
DIMENSIONS = ["dim_date", "dim_customer", "dim_product", "dim_channel", "dim_seller"]


def execute_file(connection, name):
    # All statements are repository-owned static SQL; no interpolated external inputs.
    for statement in read_statements(name):
        connection.execute(text(statement))


def read_statements(name):
    # These repository files contain only plain statements, without SQL functions/dollar quoting.
    content = (SQL_PATH / name).read_text(encoding="utf-8")
    content = "\n".join(line for line in content.splitlines() if not line.lstrip().startswith("--"))
    return [statement for statement in content.split(";") if statement.strip()]


def initialize(connection):
    inspector = inspect(connection)
    existing = {
        schema: inspector.get_table_names(schema=schema)
        for schema in ("raw", "staging", "analytics")
        if schema in inspector.get_schema_names()
    }
    if any(existing.values()):
        if "pipeline_metadata" not in existing.get("analytics", []):
            raise ValueError("Existing schemas are not owned by this project; refusing to modify")
        metadata = connection.execute(
            text("SELECT owner, contract_version FROM analytics.pipeline_metadata WHERE singleton")
        ).one_or_none()
        if metadata is None or metadata[0] != OWNER or metadata[1] not in (1, 2):
            raise ValueError("Unknown warehouse ownership/version")
        allowed = {
            "raw": set(CONTRACTS),
            "staging": set(CONTRACTS),
            "analytics": {*DIMENSIONS, "fact_sales", "pipeline_metadata", "schema_migrations"},
        }
        if any(set(tables) - allowed[schema] for schema, tables in existing.items()):
            raise ValueError("Unexpected tables in warehouse schemas; refusing to modify")
        if metadata[1] == 1:
            execute_file(connection, "migrations/002_variable_costs.sql")
    execute_file(connection, "01_create_schemas.sql")
    execute_file(connection, "00_create_source_tables.sql")
    for name in (
        "02_create_dimensions.sql",
        "03_create_fact_sales.sql",
        "04_create_indexes.sql",
        "08_discount_limit.sql",
        "05_create_views.sql",
    ):
        execute_file(connection, name)
    connection.execute(
        text("INSERT INTO analytics.schema_migrations(version) VALUES (2) ON CONFLICT DO NOTHING")
    )


def load_snapshot(connection, original, cleaned, dimensions, fact):
    """Replace only owned tables inside caller transaction; never drop tables/volumes."""
    connection.execute(text("DELETE FROM analytics.fact_sales"))
    for name in DIMENSIONS:
        connection.execute(text(f'DELETE FROM analytics."{name}"'))
    for schema, data in (("raw", original), ("staging", cleaned)):
        for name, frame in data.items():
            connection.execute(text(f'DELETE FROM {schema}."{name}"'))
            append_frame(connection, name, schema, frame)
    for name, frame in dimensions.items():
        append_frame(connection, name, "analytics", frame)
    append_frame(connection, "fact_sales", "analytics", fact)


def append_frame(connection, name, schema, frame):
    # Reflection avoids pandas inferring Decimal object columns as VARCHAR.
    table = Table(name, MetaData(), schema=schema, autoload_with=connection)
    frame.to_sql(
        name,
        connection,
        schema=schema,
        if_exists="append",
        index=False,
        chunksize=5000,
        dtype={column.name: column.type for column in table.columns},
    )


def read_fact(connection):
    return pd.read_sql(
        text("SELECT * FROM analytics.fact_sales ORDER BY sale_key"), connection, coerce_float=False
    )
