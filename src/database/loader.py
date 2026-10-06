from pathlib import Path

import pandas as pd
from sqlalchemy import Column, Date, Integer, MetaData, Numeric, String, Table, inspect, text

from src.validation.schemas import CONTRACTS

SQL_PATH = Path(__file__).resolve().parents[2] / "sql"
OWNER = "sales-profitability-intelligence"
DIMENSIONS = ["dim_date", "dim_customer", "dim_product", "dim_channel", "dim_seller"]


def execute_file(connection, name):
    # All statements are repository-owned static SQL; no interpolated external inputs.
    for statement in (SQL_PATH / name).read_text(encoding="utf-8").split(";"):
        if statement.strip():
            connection.execute(text(statement))


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
        if metadata != (OWNER, 1):
            raise ValueError("Unknown warehouse ownership/version")
        allowed = {
            "raw": set(CONTRACTS),
            "staging": set(CONTRACTS),
            "analytics": {*DIMENSIONS, "fact_sales", "pipeline_metadata"},
        }
        if any(set(tables) - allowed[schema] for schema, tables in existing.items()):
            raise ValueError("Unexpected tables in warehouse schemas; refusing to modify")
    execute_file(connection, "01_create_schemas.sql")
    metadata = MetaData()
    for schema in ("raw", "staging"):
        for name, contract in CONTRACTS.items():

            def column_type(kind):
                return {
                    "int": Integer(),
                    "date": Date(),
                    "text": String(),
                    "money": Numeric(18, 2),
                    "rate": Numeric(8, 4),
                }[kind]

            Table(
                name,
                metadata,
                *[
                    Column(
                        col,
                        String() if schema == "raw" else column_type(kind),
                        primary_key=col in contract.key,
                        nullable=False,
                    )
                    for col, kind in contract.columns.items()
                ],
                schema=schema,
            )
    metadata.create_all(connection)
    for name in (
        "02_create_dimensions.sql",
        "03_create_fact_sales.sql",
        "04_create_indexes.sql",
        "05_create_views.sql",
    ):
        execute_file(connection, name)


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
