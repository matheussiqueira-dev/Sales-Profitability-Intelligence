"""Add V2 cost source to existing V1 CSVs without changing original transactions."""

import csv
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import Settings  # noqa: E402
from src.validation.schemas import CONTRACTS  # noqa: E402


def upgrade(path, seed=42):
    target = path / "variable_costs.csv"
    if target.exists():
        return
    items = pd.read_csv(path / "order_items.csv")
    orders = pd.read_csv(path / "orders.csv").set_index("order_id")
    rates = {
        "Loja Física": (".0100", ".0000", ".0200"),
        "E-commerce": (".0320", ".0000", ".0050"),
        "Marketplace": (".0350", ".1450", ".0050"),
        "Venda Direta": (".0150", ".0000", ".0200"),
    }
    rng = random.Random(seed + 104729)
    with target.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CONTRACTS["variable_costs"].columns)
        writer.writeheader()
        for row in items.sort_values("order_item_id").itertuples():
            payment, channel, commission = rates[orders.loc[row.order_id, "channel"]]
            writer.writerow(
                {
                    "order_item_id": row.order_item_id,
                    "payment_fee_rate": payment,
                    "channel_fee_rate": channel,
                    "commission_rate": commission,
                    "packaging_cost": f"{rng.uniform(0.8, 5):.2f}",
                }
            )


if __name__ == "__main__":
    upgrade(Settings.from_env().raw_path)
