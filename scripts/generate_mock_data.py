"""Deterministic, commercially structured synthetic data; no real personal data."""

import argparse
import csv
import logging
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.validation.schemas import CHANNELS, CONTRACTS  # noqa: E402

LOG = logging.getLogger(__name__)
LOCATIONS = [
    ("São Paulo", "SP", "Sudeste"),
    ("Rio de Janeiro", "RJ", "Sudeste"),
    ("Fortaleza", "CE", "Nordeste"),
    ("Recife", "PE", "Nordeste"),
    ("Curitiba", "PR", "Sul"),
    ("Porto Alegre", "RS", "Sul"),
    ("Manaus", "AM", "Norte"),
    ("Belém", "PA", "Norte"),
    ("Goiânia", "GO", "Centro-Oeste"),
    ("Brasília", "DF", "Centro-Oeste"),
]
CATEGORIES = ["Eletrônicos", "Acessórios", "Casa", "Escritório", "Esportes", "Ferramentas"]


def generate(seed=42, orders_count=40000, customers_count=2000, products_count=200):
    if min(orders_count, customers_count, products_count) < 1:
        raise ValueError("Counts must be positive")
    rng = random.Random(seed)
    data = {name: [] for name in CONTRACTS}
    for cid in range(1, customers_count + 1):
        city, state, region = LOCATIONS[(cid - 1) % len(LOCATIONS)]
        segment = ["Enterprise", "Corporate", "SMB", "Consumer"][(cid - 1) % 4]
        data["customers"].append(
            {
                "customer_id": cid,
                "customer_name": f"Cliente Sintético {cid:04}",
                "customer_type": "B2C" if segment == "Consumer" else "B2B",
                "city": city,
                "state": state,
                "region": region,
                "segment": segment,
                "registration_date": (
                    date(2022, 1, 1) + timedelta(days=rng.randrange(700))
                ).isoformat(),
            }
        )
    for pid in range(1, products_count + 1):
        category = CATEGORIES[(pid - 1) % 6]
        price = round(
            rng.uniform(80, 3000) if category == "Eletrônicos" else rng.uniform(15, 600), 2
        )
        ratio = 0.85 if pid % 10 == 0 else (0.35 if category == "Acessórios" else 0.55)
        data["products"].append(
            {
                "product_id": pid,
                "product_name": f"{category} Produto {pid:03}",
                "category": category,
                "subcategory": f"Linha {pid % 4 + 1}",
                "unit_cost": f"{price * ratio:.2f}",
                "list_price": f"{price:.2f}",
                "supplier": f"Fornecedor Sintético {pid % 12 + 1:02}",
            }
        )
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(731)]
    dates = rng.choices(
        days,
        weights=[
            (1.8 if d.month in (11, 12) else 1) * (1.2 if d.year == 2025 else 1) for d in days
        ],
        k=orders_count,
    )
    product_weights = [5 if p["product_id"] % 10 == 0 else 1 for p in data["products"]]
    customer_weights = [8 if c["customer_id"] <= 50 else 1 for c in data["customers"]]
    for oid, day in enumerate(sorted(dates), 1):
        customer = rng.choices(data["customers"], weights=customer_weights)[0]
        channel = rng.choices(CHANNELS, weights=[20, 30, 35, 15])[0]
        cancelled = rng.random() < 0.025
        order = {
            "order_id": oid,
            "order_date": day.isoformat(),
            "customer_id": customer["customer_id"],
            "channel": channel,
            "seller_id": rng.randint(1, 16),
            "status": "cancelled" if cancelled else "completed",
        }
        quantities, returned = 0, 0
        for _ in range(rng.choices([1, 2, 3, 4], weights=[10, 40, 35, 15])[0]):
            product = rng.choices(data["products"], weights=product_weights)[0]
            qty = rng.randint(1, 5)
            discount = rng.choices(
                [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30], weights=[30, 25, 20, 12, 7, 4, 2]
            )[0]
            if customer["customer_id"] <= 50:
                discount = min(0.30, discount + 0.10)
            if day.year == 2025 and channel == "Marketplace":
                discount = min(0.30, discount + 0.05)
            if channel == "Venda Direta":
                discount = max(0, discount - 0.05)
            iid = len(data["order_items"]) + 1
            data["order_items"].append(
                {
                    "order_item_id": iid,
                    "order_id": oid,
                    "product_id": product["product_id"],
                    "quantity": qty,
                    "unit_price": product["list_price"],
                    "discount_percentage": f"{discount:.2f}",
                }
            )
            quantities += qty
            probability = 0.20 if product["product_id"] % 17 == 0 else 0.035
            if not cancelled and rng.random() < probability:
                ret_qty = rng.randint(1, qty)
                returned += ret_qty
                data["returns"].append(
                    {
                        "return_id": len(data["returns"]) + 1,
                        "order_item_id": iid,
                        "return_date": (day + timedelta(days=rng.randint(1, 30))).isoformat(),
                        "quantity_returned": ret_qty,
                        "return_reason": rng.choice(
                            [
                                "defective",
                                "wrong_item",
                                "customer_request",
                                "damaged",
                                "late_delivery",
                            ]
                        ),
                    }
                )
        if returned:
            order["status"] = "returned" if returned == quantities else "partially_returned"
        data["orders"].append(order)
        actual = rng.uniform(10, 60)
        actual *= {"Marketplace": 2.5, "Venda Direta": 0.5}.get(channel, 1)
        if customer["region"] == "Norte":
            actual *= 1.5
        data["freight"].append(
            {
                "order_id": oid,
                "freight_charged": f"{actual * 0.6:.2f}",
                "freight_actual": "0.00" if cancelled else f"{actual:.2f}",
            }
        )
    for year in (2024, 2025):
        for month in range(1, 13):
            for channel in CHANNELS:
                data["targets"].append(
                    {
                        "month": f"{year}-{month:02}-01",
                        "channel": channel,
                        "revenue_target": "500000.00",
                        "margin_target_percentage": "0.20",
                    }
                )
    # Separate RNG preserves every V1 transaction for exact before/after comparisons.
    cost_rng = random.Random(seed + 104729)
    order_channels = {order["order_id"]: order["channel"] for order in data["orders"]}
    rates = {
        "Loja Física": (".0100", ".0000", ".0200"),
        "E-commerce": (".0320", ".0000", ".0050"),
        "Marketplace": (".0350", ".1450", ".0050"),
        "Venda Direta": (".0150", ".0000", ".0200"),
    }
    for item in data["order_items"]:
        payment, channel, commission = rates[order_channels[item["order_id"]]]
        data["variable_costs"].append(
            {
                "order_item_id": item["order_item_id"],
                "payment_fee_rate": payment,
                "channel_fee_rate": channel,
                "commission_rate": commission,
                "packaging_cost": f"{cost_rng.uniform(0.8, 5):.2f}",
            }
        )
    return data


def write_dataset(data, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in data.items():
        with (output / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(CONTRACTS[name].columns))
            writer.writeheader()
            writer.writerows(rows)
        LOG.info("%s: %s rows", name, len(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--orders", type=int, default=40000)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--products", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    if args.output.exists() and any(args.output.glob("*.csv")):
        parser.error("Output already contains CSVs; choose a new --output to preserve source data")
    write_dataset(generate(args.seed, args.orders, args.customers, args.products), args.output)


if __name__ == "__main__":
    main()
