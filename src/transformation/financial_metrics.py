from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0")


def decimal(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Non-finite numeric")
    return result


def money(value):
    return decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def financial_metrics(
    quantity, unit_price, discount_percentage, unit_cost, returned_quantity=0, freight_allocated=0
):
    qty, returned = decimal(quantity), decimal(returned_quantity)
    price, cost, discount, freight = map(
        decimal, (unit_price, unit_cost, discount_percentage, freight_allocated)
    )
    if qty <= 0 or qty != qty.to_integral_value():
        raise ValueError("Quantity must be a positive integer")
    if returned < 0 or returned > qty or returned != returned.to_integral_value():
        raise ValueError("Invalid returned quantity")
    if min(price, cost, freight) < 0 or not ZERO <= discount <= 1:
        raise ValueError("Invalid price, cost, freight or discount")
    gross = money(qty * price)
    discounts = money(gross * discount)
    # A full return must refund exactly the rounded discounted line amount.
    refund = money((gross - discounts) * returned / qty)
    net = gross - discounts - refund
    cmv = money((qty - returned) * cost)
    margin = net - cmv - money(freight)
    return {
        "gross_revenue": gross,
        "discount_value": discounts,
        "return_value": refund,
        "net_revenue": net,
        "total_product_cost": cmv,
        "freight_allocated": money(freight),
        "contribution_margin": margin,
        "contribution_margin_percentage": margin / net if net else None,
    }


def allocate_freight(total, revenues, quantities):
    """Largest-remainder cents, stable item-order tie break; quantity fallback."""
    total = money(total)
    revenues = list(map(decimal, revenues))
    quantities = list(map(decimal, quantities))
    if total < 0 or not revenues or len(revenues) != len(quantities):
        raise ValueError("Invalid allocation inputs")
    if min(revenues) < 0 or min(quantities) <= 0:
        raise ValueError("Invalid weights")
    weights = revenues if sum(revenues) else quantities
    exact = [total * weight / sum(weights) for weight in weights]
    rounded = [value.quantize(CENT, rounding=ROUND_DOWN) for value in exact]
    remaining = int((total - sum(rounded)) / CENT)
    ranking = sorted(range(len(exact)), key=lambda i: (-(exact[i] - rounded[i]), i))
    for i in ranking[:remaining]:
        rounded[i] += CENT
    return rounded


def maximum_discount(price, cost, variable_cost=0, minimum_margin=Decimal(".15")):
    price, cost, variable_cost, minimum_margin = map(
        decimal, (price, cost, variable_cost, minimum_margin)
    )
    if price <= 0 or min(cost, variable_cost) < 0 or not ZERO <= minimum_margin < 1:
        raise ValueError("Invalid sustainable discount inputs")
    # Negative means even full list price cannot reach the required margin.
    return 1 - (cost + variable_cost) / (price * (1 - minimum_margin))


def simulate_discount(fact, discount):
    discount = decimal(discount)
    if not ZERO <= discount <= Decimal(".30"):
        raise ValueError("Simulator discount must be between 0 and 30%")
    net = sum(
        (
            money(
                (decimal(r.quantity) - decimal(r.returned_quantity))
                * decimal(r.unit_price)
                * (1 - discount)
            )
            for r in fact.itertuples()
        ),
        ZERO,
    )
    costs = sum(fact.total_product_cost, ZERO) + sum(fact.freight_allocated, ZERO)
    margin = net - costs
    current = sum(fact.contribution_margin, ZERO)
    return {
        "net_revenue": net,
        "margin": margin,
        "margin_percentage": margin / net if net else None,
        "margin_impact": margin - current,
        "required_volume_growth": current / margin - 1 if margin > 0 and current > 0 else None,
    }
