from datetime import timedelta

import pandas as pd

from src.validation.schemas import CHANNELS


def build_dimensions(data):
    customer = data["customers"].drop(columns="registration_date").copy()
    customer.insert(0, "customer_key", customer.customer_id)
    product = data["products"].drop(columns=["unit_cost", "list_price"]).copy()
    product.insert(0, "product_key", product.product_id)
    channel = pd.DataFrame({"channel_key": range(1, 5), "channel_name": CHANNELS})
    sellers = sorted(data["orders"].seller_id.unique())
    seller = pd.DataFrame(
        [
            {
                "seller_key": sid,
                "seller_id": sid,
                "seller_name": f"Vendedor Sintético {sid:02}",
                "region": "Nacional",
            }
            for sid in sellers
        ]
    )
    start, end = data["orders"].order_date.min(), data["orders"].order_date.max()
    start, end = start.replace(month=1, day=1), end.replace(month=12, day=31)
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    months = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    calendar = pd.DataFrame(
        [
            {
                "date_key": int(day.strftime("%Y%m%d")),
                "full_date": day,
                "day": day.day,
                "month": day.month,
                "month_name": months[day.month - 1],
                "quarter": (day.month - 1) // 3 + 1,
                "year": day.year,
                "week_of_year": day.isocalendar().week,
                "is_weekend": day.weekday() >= 5,
            }
            for day in dates
        ]
    )
    return {
        "dim_date": calendar,
        "dim_customer": customer,
        "dim_product": product,
        "dim_channel": channel,
        "dim_seller": seller,
    }
