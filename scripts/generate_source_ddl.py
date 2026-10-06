"""Render SQL source contracts once and verify drift in CI with --check."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.validation.schemas import CONTRACTS  # noqa: E402


def render():
    types = {
        "int": "integer",
        "date": "date",
        "text": "text",
        "money": "numeric(18,2)",
        "rate": "numeric(8,4)",
    }
    statements = ["-- Generated from CONTRACTS, committed DDL is the physical source of truth."]
    for schema in ("raw", "staging"):
        for name, contract in CONTRACTS.items():
            columns = []
            for col, kind in contract.columns.items():
                dtype = "text" if schema == "raw" else types[kind]
                constraint = ""
                if schema == "staging" and kind in ("int", "money", "rate"):
                    condition = f"{col} > 0" if kind == "int" else f"{col} >= 0"
                    if kind == "rate":
                        condition += f" AND {col} <= 1"
                    constraint = f" CHECK({condition})"
                columns.append(f"    {col} {dtype} NOT NULL{constraint}")
            columns.append(f"    PRIMARY KEY ({', '.join(contract.key)})")
            if schema == "staging" and name == "variable_costs":
                columns.append(
                    "    CHECK(payment_fee_rate + channel_fee_rate + commission_rate < 1)"
                )
            statements.append(
                f"CREATE TABLE IF NOT EXISTS {schema}.{name} (\n" + ",\n".join(columns) + "\n);"
            )
    return "\n".join(statements) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "sql/00_create_source_tables.sql"
    expected = render()
    if args.check:
        if path.read_text(encoding="utf-8") != expected:
            raise SystemExit("Source DDL differs from CONTRACTS")
    else:
        path.write_text(expected, encoding="utf-8")
