"""Declarative exact-value contracts; Decimal objects never coerced to float."""

from datetime import date
from decimal import Decimal

import pandera.pandas as pa

from src.validation.schemas import CHANNELS, CONTRACTS, STATUSES


def field_valid(value, kind):
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool) and 0 < value <= 2147483647
    if kind in ("money", "rate"):
        if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
            return False
        scale = Decimal(".01") if kind == "money" else Decimal(".0001")
        return (
            value == value.quantize(scale)
            and value < Decimal("1e16")
            and (kind != "rate" or value <= 1)
        )
    if kind == "date":
        return isinstance(value, date)
    return isinstance(value, str) and bool(value.strip())


def schema_for(name):
    contract = CONTRACTS[name]
    columns = {}
    for col, kind in contract.columns.items():
        checks = [pa.Check(lambda value, kind=kind: field_valid(value, kind), element_wise=True)]
        if col == "channel":
            checks.append(pa.Check.isin(CHANNELS))
        if name == "orders" and col == "status":
            checks.append(pa.Check.isin(STATUSES))
        columns[col] = pa.Column(object, checks=checks, nullable=False, coerce=False)
    extra = []
    if name == "products":
        extra.append(pa.Check(lambda frame: frame.unit_cost < frame.list_price))
    if name == "variable_costs":
        extra.append(
            pa.Check(
                lambda frame: (
                    frame.payment_fee_rate + frame.channel_fee_rate + frame.commission_rate < 1
                )
            )
        )
    return pa.DataFrameSchema(
        columns, checks=extra, strict=True, unique=list(contract.key), name=name
    )


def validate_with_pandera(data):
    failures = []
    for name, frame in data.items():
        try:
            schema_for(name).validate(frame, lazy=True)
        except pa.errors.SchemaErrors as exc:
            for row in exc.failure_cases.itertuples():
                failures.append(f"{name}.{row.column}: Pandera check {row.check}")
    return failures
