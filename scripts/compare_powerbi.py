"""Compare actual Desktop DAX results with independent Python/PostgreSQL values."""

import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import ROOT, Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402
from src.database.loader import read_fact  # noqa: E402
from src.transformation.financial_metrics import simulate_discount  # noqa: E402


def main():
    baseline = json.loads(
        (ROOT / "artifacts/powerbi-dax-results.json").read_text(encoding="utf-8-sig")
    )
    scenarios = json.loads(
        (ROOT / "artifacts/powerbi-scenarios.json").read_text(encoding="utf-8-sig")
    )
    engine = engine_for(Settings.from_env())
    try:
        with engine.connect() as connection:
            fact = read_fact(connection)
        metrics = [
            "gross_revenue",
            "discount_value",
            "return_value",
            "net_revenue",
            "total_product_cost",
            "freight_allocated",
            "variable_cost_value",
            "contribution_margin",
        ]
        comparisons = []
        for name in metrics:
            python = sum(fact[name], Decimal(0))
            dax = Decimal(baseline[f"[{name}]"])
            comparisons.append(
                {
                    "metric": name,
                    "python_sql": str(python),
                    "dax": str(dax),
                    "difference": str(dax - python),
                }
            )
        simulations = []
        for row in scenarios:
            discount = Decimal(row["Desconto Simulado[Value]"])
            expected = simulate_discount(fact, discount)
            differences = {
                name: str(Decimal(row[f"[{name}]"]) - expected[name])
                for name in ("net_revenue", "variable_cost_value", "margin")
            }
            simulations.append(
                {
                    "discount": str(discount),
                    "python": {k: str(v) for k, v in expected.items()},
                    "dax": row,
                    "differences": differences,
                }
            )
        passed = (
            len(scenarios) == 4
            and all(Decimal(r["difference"]) == 0 for r in comparisons)
            and all(Decimal(v) == 0 for row in simulations for v in row["differences"].values())
        )
        report = {
            "passed": passed,
            "source": "Desktop local Analysis Services via ADOMD",
            "baseline": comparisons,
            "scenarios": simulations,
        }
        (ROOT / "artifacts/powerbi-parity.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        if not passed:
            raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
