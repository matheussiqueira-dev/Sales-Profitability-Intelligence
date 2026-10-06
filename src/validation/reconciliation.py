from decimal import Decimal

from sqlalchemy import text

from src.transformation.financial_metrics import CENT, ZERO


def source_totals(data):
    """Independent source aggregation; does not call transformation helpers."""
    orders = data["orders"].set_index("order_id")
    products = data["products"].set_index("product_id")
    returns = data["returns"].groupby("order_item_id").quantity_returned.sum().to_dict()
    totals = dict.fromkeys(
        [
            "gross_revenue",
            "discount_value",
            "return_value",
            "net_revenue",
            "total_product_cost",
            "freight_allocated",
            "contribution_margin",
        ],
        ZERO,
    )
    active = set(orders[orders.status != "cancelled"].index)
    for item in data["order_items"].itertuples():
        if item.order_id not in active:
            continue
        gross = (item.quantity * item.unit_price).quantize(CENT, rounding="ROUND_HALF_UP")
        discount = (gross * item.discount_percentage).quantize(CENT, rounding="ROUND_HALF_UP")
        returned = returns.get(item.order_item_id, 0)
        refund = ((gross - discount) * returned / item.quantity).quantize(
            CENT, rounding="ROUND_HALF_UP"
        )
        cost = ((item.quantity - returned) * products.loc[item.product_id, "unit_cost"]).quantize(
            CENT, rounding="ROUND_HALF_UP"
        )
        for col, value in (
            ("gross_revenue", gross),
            ("discount_value", discount),
            ("return_value", refund),
            ("net_revenue", gross - discount - refund),
            ("total_product_cost", cost),
        ):
            totals[col] += value
    totals["freight_allocated"] = sum(
        (r.freight_actual for r in data["freight"].itertuples() if r.order_id in active), ZERO
    )
    totals["contribution_margin"] = (
        totals["net_revenue"] - totals["total_product_cost"] - totals["freight_allocated"]
    )
    return totals


def reconcile(data, warehouse, tolerance=Decimal("0.00")):
    expected = source_totals(data)
    report = {"passed": True, "metrics": {}}
    for metric, value in expected.items():
        actual = sum(warehouse[metric], ZERO)
        difference = actual - value
        report["metrics"][metric] = {
            "source": str(value),
            "warehouse": str(actual),
            "difference": str(difference),
        }
        report["passed"] &= abs(difference) <= tolerance
    expected_ids = set(
        data["order_items"][
            data["order_items"].order_id.isin(
                data["orders"][data["orders"].status != "cancelled"].order_id
            )
        ].order_item_id
    )
    report["rows"] = {"source": len(expected_ids), "warehouse": len(warehouse)}
    report["passed"] &= set(warehouse.order_item_id) == expected_ids
    report["passed"] &= len(warehouse) == len(expected_ids)
    # Verify each order freight independently, so global cancellation cannot hide drift.
    actual_freight = warehouse.groupby("order_id").freight_allocated.sum()
    expected_freight = data["freight"].set_index("order_id").freight_actual
    report["freight_orders_passed"] = all(
        actual == expected_freight.loc[oid] for oid, actual in actual_freight.items()
    )
    report["passed"] &= report["freight_orders_passed"]
    return report


def reconcile_sql(connection, report):
    from src.database.loader import SQL_PATH

    query = (SQL_PATH / "06_validation_queries.sql").read_text(encoding="utf-8")
    source = connection.execute(text(query)).mappings().one()
    report["sql_source_passed"] = all(
        value == Decimal(report["metrics"][metric]["warehouse"]) for metric, value in source.items()
    )
    report["passed"] &= report["sql_source_passed"]
    return report
