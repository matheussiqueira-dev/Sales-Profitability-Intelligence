from decimal import Decimal

import pandas as pd
import pytest

from src.transformation.financial_metrics import (
    aggregate_discount_limit,
    financial_metrics,
    maximum_discount,
    simulate_discount,
)
from src.validation.quality import QualityError, validate_sources


def test_variable_fees_and_packaging():
    result = financial_metrics(
        2, 100, ".10", 60, 1, 7, variable_cost_rate=".185", variable_cost_fixed=3
    )
    assert result["net_revenue"] == 90
    assert result["variable_cost_value"] == Decimal("19.65")
    assert result["contribution_margin"] == Decimal("3.35")
    returned = financial_metrics(
        1, 100, 0, 60, 1, 7, variable_cost_rate=".185", variable_cost_fixed=3
    )
    assert returned["variable_cost_value"] == 3
    assert returned["contribution_margin"] == -10
    assert returned["contribution_margin_percentage"] is None


def test_fee_aware_discount_ceiling():
    result = maximum_discount(100, 63, 7, ".15", variable_cost_rate=".10")
    assert abs(result - Decimal(".0666666666666666666666666667")) < Decimal("1e-25")
    assert maximum_discount(100, 63, 7, ".80", variable_cost_rate=".20") is None


def test_heterogeneous_rates_weight_undiscounted_base():
    fact = pd.DataFrame(
        [
            {
                "quantity": 1,
                "returned_quantity": 0,
                "unit_price": Decimal(100),
                "variable_cost_rate": Decimal(".2"),
                "variable_cost_fixed": Decimal(0),
                "total_product_cost": Decimal(40),
                "freight_allocated": Decimal(0),
                "contribution_margin": Decimal(16),
            },
            {
                "quantity": 1,
                "returned_quantity": 0,
                "unit_price": Decimal(100),
                "variable_cost_rate": Decimal(0),
                "variable_cost_fixed": Decimal(0),
                "total_product_cost": Decimal(40),
                "freight_allocated": Decimal(0),
                "contribution_margin": Decimal(60),
            },
        ]
    )
    ceiling = aggregate_discount_limit(fact, ".15")
    assert ceiling == Decimal(1) - Decimal(80) / (Decimal(200) * Decimal(".75"))
    result = simulate_discount(fact, ".20")
    assert result["variable_cost_value"] == 16
    assert result["margin"] == 64
    assert result["required_volume_growth"] == Decimal(76) / 64 - 1


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "rate", "negative"])
def test_cost_contract_rejected(sources, mutation):
    if mutation == "missing":
        sources["variable_costs"] = sources["variable_costs"].iloc[1:]
    elif mutation == "duplicate":
        sources["variable_costs"].loc[1, "order_item_id"] = (
            sources["variable_costs"].iloc[0].order_item_id
        )
    elif mutation == "rate":
        sources["variable_costs"].loc[0, "channel_fee_rate"] = "1.0"
    else:
        sources["variable_costs"].loc[0, "packaging_cost"] = "-1"
    with pytest.raises(QualityError):
        validate_sources(sources)
