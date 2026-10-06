from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    key: tuple[str, ...]
    columns: dict[str, str]


CONTRACTS = {
    "customers": Contract(
        ("customer_id",),
        {
            "customer_id": "int",
            "customer_name": "text",
            "customer_type": "text",
            "city": "text",
            "state": "text",
            "region": "text",
            "registration_date": "date",
            "segment": "text",
        },
    ),
    "products": Contract(
        ("product_id",),
        {
            "product_id": "int",
            "product_name": "text",
            "category": "text",
            "subcategory": "text",
            "unit_cost": "money",
            "list_price": "money",
            "supplier": "text",
        },
    ),
    "orders": Contract(
        ("order_id",),
        {
            "order_id": "int",
            "order_date": "date",
            "customer_id": "int",
            "channel": "text",
            "seller_id": "int",
            "status": "text",
        },
    ),
    "order_items": Contract(
        ("order_item_id",),
        {
            "order_item_id": "int",
            "order_id": "int",
            "product_id": "int",
            "quantity": "int",
            "unit_price": "money",
            "discount_percentage": "rate",
        },
    ),
    "returns": Contract(
        ("return_id",),
        {
            "return_id": "int",
            "order_item_id": "int",
            "return_date": "date",
            "quantity_returned": "int",
            "return_reason": "text",
        },
    ),
    "freight": Contract(
        ("order_id",),
        {
            "order_id": "int",
            "freight_charged": "money",
            "freight_actual": "money",
        },
    ),
    "targets": Contract(
        ("month", "channel"),
        {
            "month": "date",
            "channel": "text",
            "revenue_target": "money",
            "margin_target_percentage": "rate",
        },
    ),
}
CHANNELS = ["Loja Física", "E-commerce", "Marketplace", "Venda Direta"]
STATUSES = ["completed", "returned", "partially_returned", "cancelled"]
