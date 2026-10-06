import pandas as pd
import pytest

from scripts.generate_mock_data import generate
from src.validation.quality import QualityError, validate_sources


def test_deterministic_generator_and_valid_contracts(sources):
    assert generate(8, 20, 10, 10) == generate(8, 20, 10, 10)
    _, report = validate_sources(sources)
    assert report["passed"]
    assert all(t["duplicates"] == 0 for t in report["tables"].values())


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("customers", "customer_id", None),
        ("orders", "customer_id", 99999),
        ("orders", "channel", "Unknown"),
        ("order_items", "product_id", 99999),
        ("order_items", "quantity", 0),
        ("order_items", "quantity", -1),
        ("order_items", "quantity", "1.5"),
        ("order_items", "unit_price", "-1"),
        ("products", "unit_cost", "-1"),
        ("order_items", "discount_percentage", "1.01"),
        ("order_items", "discount_percentage", "-0.01"),
        ("order_items", "unit_price", "NaN"),
        ("order_items", "unit_price", "Infinity"),
        ("order_items", "unit_price", "1.001"),
        ("orders", "order_date", "2024-02-30"),
        ("orders", "order_date", "2020-01-01"),
        ("targets", "month", "2024-01-02"),
        ("products", "unit_cost", "99999999"),
    ],
)
def test_invalid_sources_rejected(sources, table, column, value):
    sources[table] = sources[table].astype(object)
    sources[table].loc[0, column] = value
    with pytest.raises(QualityError) as error:
        validate_sources(sources)
    assert not error.value.report["passed"]


def test_duplicate_primary_key(sources):
    sources["customers"] = pd.concat([sources["customers"], sources["customers"].iloc[:1]])
    with pytest.raises(QualityError):
        validate_sources(sources)


def test_cumulative_returns_cannot_exceed_sale(sources):
    iid = sources["order_items"].iloc[0].order_item_id
    quantity = sources["order_items"].iloc[0].quantity
    sources["returns"] = pd.DataFrame(
        [
            {
                "return_id": n,
                "order_item_id": iid,
                "return_date": "2026-01-01",
                "quantity_returned": quantity,
                "return_reason": "defective",
            }
            for n in (1, 2)
        ]
    )
    with pytest.raises(QualityError) as error:
        validate_sources(sources)
    assert any("cumulative" in e for e in error.value.report["errors"])


def test_missing_freight_and_columns(sources):
    sources["freight"] = sources["freight"].iloc[1:]
    with pytest.raises(QualityError):
        validate_sources(sources)
    sources["products"] = sources["products"].drop(columns="supplier")
    with pytest.raises(QualityError):
        validate_sources(sources)
