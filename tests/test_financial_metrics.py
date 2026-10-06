from decimal import Decimal

import pandas as pd
import pytest

from src.transformation.financial_metrics import (
    allocate_freight,
    financial_metrics,
    maximum_discount,
    simulate_discount,
)


@pytest.mark.parametrize(
    "discount,returned,freight,net,cmv,margin",
    [
        (0, 0, 0, "200.00", "120.00", "80.00"),
        (0.10, 0, 0, "180.00", "120.00", "60.00"),
        (0.10, 1, 0, "90.00", "60.00", "30.00"),
        (0.10, 2, 7, "0.00", "0.00", "-7.00"),
        (0, 0, 20, "200.00", "120.00", "60.00"),
        (0.50, 0, 10, "100.00", "120.00", "-30.00"),
        (1, 0, 10, "0.00", "120.00", "-130.00"),
    ],
)
def test_financial_examples(discount, returned, freight, net, cmv, margin):
    result = financial_metrics(2, 100, discount, 60, returned, freight)
    assert result["net_revenue"] == Decimal(net)
    assert result["total_product_cost"] == Decimal(cmv)
    assert result["contribution_margin"] == Decimal(margin)
    assert (result["contribution_margin_percentage"] is None) == (Decimal(net) == 0)


@pytest.mark.parametrize(
    "args",
    [
        (0, 100, 0, 60),
        (-1, 100, 0, 60),
        (1.5, 100, 0, 60),
        (1, 100, -0.1, 60),
        (1, 100, 1.1, 60),
        (1, -100, 0, 60),
        (1, 100, 0, -60),
        (1, 100, 0, 60, 2),
        (1, 100, 0, 60, -0.5),
        (1, "NaN", 0, 60),
        (1, 100, 0, 60, 0, -1),
    ],
)
def test_invalid_metrics(args):
    with pytest.raises(ValueError):
        financial_metrics(*args)


def test_full_return_rounding_exact_refund():
    result = financial_metrics(3, "0.05", ".10", "0.02", 3)
    assert result["discount_value"] == Decimal(".02")
    assert result["return_value"] == Decimal(".13")
    assert result["net_revenue"] == 0


def test_freight_remainder_and_zero_revenue_fallback():
    assert allocate_freight(".05", [1, 1, 1], [1, 1, 1]) == [
        Decimal(".02"),
        Decimal(".02"),
        Decimal(".01"),
    ]
    assert allocate_freight("10", [0, 0], [1, 3]) == [Decimal("2.50"), Decimal("7.50")]


@pytest.mark.parametrize(
    "args", [(-1, [1], [1]), (1, [], []), (1, [-1], [1]), (1, [1], [0]), (1, [1, 2], [1])]
)
def test_invalid_allocation(args):
    with pytest.raises(ValueError):
        allocate_freight(*args)


def test_discount_ceiling_uses_net_margin_denominator():
    ceiling = maximum_discount(100, 63, 7, ".15")
    assert abs(ceiling - Decimal(".1764705882352941176470588235")) < Decimal("1e-25")
    revenue = Decimal(100) * (1 - ceiling)
    assert abs((revenue - 70) / revenue - Decimal(".15")) < Decimal("1e-25")
    assert maximum_discount(100, 95, 7, ".15") < 0


@pytest.mark.parametrize("args", [(0, 10), (100, -1), (100, 1, -1), (100, 1, 0, 1)])
def test_invalid_ceiling(args):
    with pytest.raises(ValueError):
        maximum_discount(*args)


def test_simulator_and_compensating_volume():
    fact = pd.DataFrame(
        [
            {
                "quantity": 2,
                "returned_quantity": 0,
                "unit_price": Decimal(100),
                "total_product_cost": Decimal(120),
                "freight_allocated": Decimal(10),
                "contribution_margin": Decimal(50),
            }
        ]
    )
    result = simulate_discount(fact, ".20")
    assert result["net_revenue"] == 160
    assert result["margin"] == 30
    assert result["margin_impact"] == -20
    assert result["required_volume_growth"] == Decimal(50) / 30 - 1
    with pytest.raises(ValueError):
        simulate_discount(fact, ".31")
