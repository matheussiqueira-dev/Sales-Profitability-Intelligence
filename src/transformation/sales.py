import pandas as pd

from src.transformation.financial_metrics import allocate_freight, financial_metrics
from src.validation.schemas import CHANNELS


def build_fact(data):
    returns = data["returns"].groupby("order_item_id").quantity_returned.sum().to_dict()
    frame = data["order_items"].merge(data["orders"], on="order_id", validate="many_to_one")
    frame = frame[frame.status != "cancelled"].copy()
    frame = frame.merge(
        data["products"][["product_id", "unit_cost"]], on="product_id", validate="many_to_one"
    )
    frame = frame.merge(data["variable_costs"], on="order_item_id", validate="one_to_one")
    freight = data["freight"].set_index("order_id").freight_actual.to_dict()
    rows = []
    for row in frame.sort_values(["order_id", "order_item_id"]).itertuples():
        returned = returns.get(row.order_item_id, 0)
        values = financial_metrics(
            row.quantity,
            row.unit_price,
            row.discount_percentage,
            row.unit_cost,
            returned,
            variable_cost_rate=row.payment_fee_rate + row.channel_fee_rate + row.commission_rate,
            variable_cost_fixed=row.packaging_cost,
        )
        rows.append(
            {
                "sale_key": row.order_item_id,
                "order_id": row.order_id,
                "order_item_id": row.order_item_id,
                "date_key": int(row.order_date.strftime("%Y%m%d")),
                "customer_key": row.customer_id,
                "product_key": row.product_id,
                "channel_key": CHANNELS.index(row.channel) + 1,
                "seller_key": row.seller_id,
                "quantity": row.quantity,
                "unit_price": row.unit_price,
                "discount_percentage": row.discount_percentage,
                "unit_cost": row.unit_cost,
                "returned_quantity": returned,
                **values,
            }
        )
    fact = pd.DataFrame(rows)
    if fact.empty:
        raise ValueError("No completed sales to load")
    for oid, group in fact.groupby("order_id", sort=False):
        allocation = allocate_freight(freight[oid], group.net_revenue, group.quantity)
        for idx, amount in zip(group.index, allocation, strict=True):
            net = fact.at[idx, "net_revenue"]
            margin = (
                net
                - fact.at[idx, "total_product_cost"]
                - amount
                - fact.at[idx, "variable_cost_value"]
            )
            fact.at[idx, "freight_allocated"] = amount
            fact.at[idx, "contribution_margin"] = margin
            fact.at[idx, "contribution_margin_percentage"] = margin / net if net else None
    return fact
