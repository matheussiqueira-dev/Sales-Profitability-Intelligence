"""Publish only reconciled, aggregated synthetic snapshots; manifest swaps atomically."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path

from src.config.settings import ROOT


def export_web_snapshot(tables, completed_at, output=ROOT / "web/public/data"):
    customers = tables["customer_profitability"]
    segments = []
    for segment, group in customers.groupby("profitability_segment"):
        segments.append(
            {
                "segment": segment,
                "customers": len(group),
                "net_revenue": sum(group.net_revenue, Decimal(0)),
                "contribution_margin": sum(group.contribution_margin, Decimal(0)),
            }
        )
    product_columns = [
        "product_name",
        "category",
        "net_revenue",
        "contribution_margin",
        "margin_percentage",
        "quantity",
        "variable_cost_value",
        "return_rate",
    ]
    payloads = {
        "executive-summary": tables["sales_summary"].to_dict("records")[0],
        "monthly-profitability": tables["monthly_performance"]
        .sort_values("month")
        .to_dict("records"),
        "channels": tables["channel_profitability"].to_dict("records"),
        "products": tables["product_profitability"][product_columns].to_dict("records"),
        "customer-segments": segments,
    }
    contents = {
        name: json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        for name, value in payloads.items()
    }
    hashes = {
        name: hashlib.sha256(content.encode()).hexdigest() for name, content in contents.items()
    }
    snapshot = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    folder = Path(output) / "snapshots" / snapshot
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        (folder / f"{name}.json").write_text(content, encoding="utf-8")
    manifest = {
        "contract_version": 2,
        "synthetic": True,
        "reconciled": True,
        "completed_at": str(completed_at),
        "snapshot": snapshot,
        "sha256": hashes,
        "period": {"from": "2024-01-01", "to": "2025-12-31"},
    }
    # Determine period from actual months, instead of inventing dataset dates.
    months = tables["monthly_performance"].month
    manifest["period"] = {"from": str(months.min()), "through_month": str(months.max())}
    temporary = Path(output) / "manifest.tmp"
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(Path(output) / "manifest.json")
    return manifest
