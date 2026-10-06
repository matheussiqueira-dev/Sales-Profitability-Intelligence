from decimal import Decimal

from src.transformation.dimensions import build_dimensions
from src.transformation.sales import build_fact
from src.validation.reconciliation import reconcile


def test_fact_grain_cancelled_excluded_and_exact_reconciliation(cleaned):
    fact = build_fact(cleaned)
    assert fact.order_item_id.is_unique
    cancelled = cleaned["orders"][cleaned["orders"].status == "cancelled"].order_id
    assert not fact.order_id.isin(cancelled).any()
    assert reconcile(cleaned, fact)["passed"]
    dimensions = build_dimensions(cleaned)
    dates = dimensions["dim_date"]
    assert dates.full_date.is_unique
    assert len(dates) == 731
    assert fact.date_key.isin(dates.date_key).all()


def test_reconciliation_detects_corruption(cleaned):
    fact = build_fact(cleaned)
    fact.loc[0, "gross_revenue"] += Decimal(".01")
    assert not reconcile(cleaned, fact)["passed"]
