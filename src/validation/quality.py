from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd

from src.validation.schemas import CHANNELS, CONTRACTS, STATUSES


class QualityError(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__("Source data rejected; inspect quality-report.json")


def validate_sources(sources):
    """Parse without lossy coercion and collect all structural/relationship errors."""
    report = {"passed": True, "tables": {}, "errors": []}
    cleaned = {}

    def issue(message):
        report["passed"] = False
        report["errors"].append(message)

    for name, contract in CONTRACTS.items():
        if name not in sources:
            issue(f"{name}: missing source")
            continue
        frame = sources[name].copy()
        report["tables"][name] = {"rows": len(frame), "duplicates": 0, "null_ids": 0}
        if set(frame.columns) != set(contract.columns):
            issue(f"{name}: columns do not match contract")
            continue
        if frame.empty and name != "returns":
            issue(f"{name}: empty source")
        for col, kind in contract.columns.items():
            values = []
            for value in frame[col]:
                try:
                    if pd.isna(value) or not str(value).strip():
                        raise ValueError("null")
                    value = str(value).strip()
                    if kind == "int":
                        value = int(value)
                        if value <= 0 or value > 2147483647:
                            raise ValueError("integer outside positive int32")
                    elif kind in ("money", "rate"):
                        value = Decimal(value)
                        if not value.is_finite() or value < 0:
                            raise ValueError("invalid numeric")
                        scale = 2 if kind == "money" else 4
                        if value != value.quantize(Decimal(10) ** -scale):
                            raise ValueError("excess decimal precision")
                        if value >= Decimal("10000000000000000"):
                            raise ValueError("numeric out of range")
                        if kind == "rate" and value > 1:
                            raise ValueError("rate outside [0,1]")
                    elif kind == "date":
                        value = date.fromisoformat(value)
                    values.append(value)
                except (ValueError, InvalidOperation, TypeError, OverflowError):
                    issue(f"{name}.{col}: invalid value at row {len(values) + 1}")
                    values.append(None)
            frame[col] = pd.Series(values, index=frame.index, dtype=object)
        keys = list(contract.key)
        duplicates = int(frame.duplicated(keys).sum())
        nulls = int(frame[keys].isna().any(axis=1).sum())
        report["tables"][name].update(duplicates=duplicates, null_ids=nulls)
        if duplicates or nulls:
            issue(f"{name}: duplicate or null primary keys")
        cleaned[name] = frame
    if not report["passed"]:
        raise QualityError(report)

    relationships = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("freight", "order_id", "orders", "order_id"),
        ("returns", "order_item_id", "order_items", "order_item_id"),
    ]
    for child, fk, parent, pk in relationships:
        if not cleaned[child][fk].isin(cleaned[parent][pk]).all():
            issue(f"{child}.{fk}: invalid foreign key")
    for table in ("orders", "targets"):
        if not cleaned[table]["channel"].isin(CHANNELS).all():
            issue(f"{table}: unknown channel")
    if not cleaned["orders"]["status"].isin(STATUSES).all():
        issue("orders: unknown status")
    products = cleaned["products"]
    if not (products.unit_cost < products.list_price).all():
        issue("products: cost must be lower than list price")
    orders = cleaned["orders"]
    if set(cleaned["freight"].order_id) != set(orders.order_id):
        issue("freight: must contain exactly one row per order")
    items = cleaned["order_items"]
    if set(items.order_id) != set(orders.order_id):
        issue("orders: every order must have items")
    customer_dates = cleaned["customers"].set_index("customer_id").registration_date
    if any(
        row.order_date < customer_dates.get(row.customer_id, date.max)
        for row in orders.itertuples()
    ):
        issue("orders: date precedes customer registration")
    if not cleaned["customers"].segment.isin(["Enterprise", "Corporate", "SMB", "Consumer"]).all():
        issue("customers: unknown segment")
    if (
        not cleaned["returns"]
        .return_reason.isin(
            [
                "defective",
                "wrong_item",
                "customer_request",
                "damaged",
                "late_delivery",
            ]
        )
        .all()
    ):
        issue("returns: unknown reason")
    if any(d.day != 1 for d in cleaned["targets"].month):
        issue("targets: month must be first day")
    returns = cleaned["returns"]
    total_returns = returns.groupby("order_item_id").quantity_returned.sum()
    item_lookup = items.set_index("order_item_id")
    order_lookup = orders.set_index("order_id")
    for iid, qty in total_returns.items():
        if iid in item_lookup.index and qty > item_lookup.loc[iid, "quantity"]:
            issue("returns: cumulative quantity exceeds sold quantity")
    for row in returns.itertuples():
        if row.order_item_id in item_lookup.index:
            oid = item_lookup.loc[row.order_item_id, "order_id"]
            if oid in order_lookup.index and row.return_date < order_lookup.loc[oid, "order_date"]:
                issue("returns: date precedes sale")
    returned_by_order = (
        items.assign(returned=items.order_item_id.map(total_returns).fillna(0))
        .groupby("order_id")
        .returned.sum()
    )
    sold_by_order = items.groupby("order_id").quantity.sum()
    for row in orders.itertuples():
        ret = returned_by_order.get(row.order_id, 0)
        sold = sold_by_order.get(row.order_id, 0)
        expected = (
            "returned" if ret == sold and sold else ("partially_returned" if ret else "completed")
        )
        if row.status == "cancelled":
            if ret:
                issue("returns: cancelled order has a return")
        elif row.status != expected:
            issue("orders: status inconsistent with returns")
    if not report["passed"]:
        raise QualityError(report)
    return cleaned, report
