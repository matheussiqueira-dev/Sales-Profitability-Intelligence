"""Output modules (insights, web export, simulator CLI) on small in-memory tables."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import create_engine

from src.analytics import simulator
from src.analytics.insights import generate_insights, read_analytics
from src.analytics.web_export import export_web_snapshot

D = Decimal


def tables(**overrides):
    base = {
        "sales_summary": pd.DataFrame(
            [
                {
                    "net_revenue": D("1000"),
                    "contribution_margin": D("200"),
                    "margin_percentage": D("0.20"),
                    "return_rate": D("0.02"),
                }
            ]
        ),
        "product_profitability": pd.DataFrame(
            [
                {
                    "product_key": 2,
                    "product_name": "Caro",
                    "category": "A",
                    "net_revenue": D("100"),
                    "contribution_margin": D("-5"),
                    "margin_percentage": D("-0.05"),
                    "quantity": 40,
                    "variable_cost_value": D("3"),
                    "return_rate": D("0.10"),
                    "maximum_discount_for_15pct_margin": D("-0.01"),
                },
                {
                    "product_key": 1,
                    "product_name": "Bom",
                    "category": "B",
                    "net_revenue": D("900"),
                    "contribution_margin": D("205"),
                    "margin_percentage": D("0.23"),
                    "quantity": 10,
                    "variable_cost_value": D("9"),
                    "return_rate": D("0.01"),
                    "maximum_discount_for_15pct_margin": None,
                },
            ]
        ),
        "customer_profitability": pd.DataFrame(
            [
                {
                    "customer_name": "Ana",
                    "net_revenue": D("100"),
                    "contribution_margin": D("1"),
                    "discount_percentage": D("0.25"),
                    "profitability_segment": "At Risk",
                    "last_order_date": date(2026, 1, 1),
                },
                {
                    "customer_name": "Bia",
                    "net_revenue": D("900"),
                    "contribution_margin": D("199"),
                    "discount_percentage": D("0.05"),
                    "profitability_segment": "Core",
                    "last_order_date": date(2026, 9, 1),
                },
            ]
        ),
        "channel_profitability": pd.DataFrame(
            [
                {
                    "channel_key": 2,
                    "channel_name": "Marketplace",
                    "net_revenue": D("500"),
                    "margin_percentage": D("0.10"),
                    "freight_allocated": D("50"),
                },
                {
                    "channel_key": 1,
                    "channel_name": "Sem vendas",
                    "net_revenue": D("0"),
                    "margin_percentage": None,
                    "freight_allocated": D("0"),
                },
            ]
        ),
        "monthly_performance": pd.DataFrame(
            [
                {
                    "month": "2026-02",
                    "net_revenue": D("120"),
                    "margin_percentage": D("0.10"),
                },
                {
                    "month": "2026-01",
                    "net_revenue": D("100"),
                    "margin_percentage": D("0.20"),
                },
            ]
        ),
        "target_performance": pd.DataFrame(
            [
                {"month": "2026-01", "channel": "Loja", "revenue_attainment": D("0.50")},
                {"month": "2026-02", "channel": "Loja", "revenue_attainment": None},
            ]
        ),
    }
    return {**base, **overrides}


def alerts_of(result, rule):
    return [alert for alert in result["alerts"] if alert["rule"] == rule]


def test_every_rule_runs_and_fires_on_its_trigger():
    result = generate_insights(tables())

    assert len(result["rules_evaluated"]) == 10
    fired = {alert["rule"] for alert in result["alerts"]}
    assert fired == set(result["rules_evaluated"])
    assert result["alerts_count"] == len(result["alerts"])


def test_alerts_name_the_entity_and_keep_evidence_as_text():
    result = generate_insights(tables())

    assert [a["entity"] for a in alerts_of(result, "negative_product_margin")] == ["Caro"]
    assert [a["entity"] for a in alerts_of(result, "customer_at_risk")] == ["Ana"]
    assert [a["entity"] for a in alerts_of(result, "revenue_target_missed")] == ["2026-01/Loja"]
    concentration = alerts_of(result, "customer_revenue_margin_concentration")[0]
    assert concentration["evidence"] == {"revenue_share": "0.1", "margin_share": "0.005"}


def test_months_are_compared_in_calendar_order():
    result = generate_insights(tables())
    assert [a["entity"] for a in alerts_of(result, "revenue_up_margin_down")] == ["2026-02"]


def test_zero_revenue_summary_skips_concentration_and_keeps_rule_listed():
    summary = pd.DataFrame(
        [
            {
                "net_revenue": D("0"),
                "contribution_margin": D("0"),
                "margin_percentage": None,
                "return_rate": D("0.02"),
            }
        ]
    )
    channels = tables()["channel_profitability"].iloc[[1]]
    result = generate_insights(tables(sales_summary=summary, channel_profitability=channels))

    assert "customer_revenue_margin_concentration" in result["rules_evaluated"]
    assert alerts_of(result, "customer_revenue_margin_concentration") == []
    assert alerts_of(result, "channel_low_margin") == []


def test_read_analytics_loads_every_view_without_float_coercion():
    engine = create_engine("sqlite://")
    views = {
        "sales_summary",
        "product_profitability",
        "customer_profitability",
        "channel_profitability",
        "monthly_performance",
        "return_analysis",
        "target_performance",
    }
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH ':memory:' AS analytics")
        for view in views:
            connection.exec_driver_sql(f"CREATE TABLE analytics.vw_{view} (value TEXT)")
            connection.exec_driver_sql(f"INSERT INTO analytics.vw_{view} VALUES ('1.10')")
        loaded = read_analytics(connection)

    assert set(loaded) == views
    assert loaded["sales_summary"].value.tolist() == ["1.10"]


def export_tables():
    data = tables()
    data["sales_summary"] = data["sales_summary"].assign(orders=2)
    return data


def test_export_writes_hashed_snapshot_and_manifest(tmp_path):
    manifest = export_web_snapshot(export_tables(), "2026-11-02T00:00:00", tmp_path)

    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest
    assert not (tmp_path / "manifest.tmp").exists()
    assert manifest["synthetic"] is True
    assert manifest["reconciled"] is True
    assert manifest["period"] == {"from": "2026-01", "through_month": "2026-02"}
    folder = tmp_path / "snapshots" / manifest["snapshot"]
    assert {path.stem for path in folder.iterdir()} == set(manifest["sha256"])
    for name, digest in manifest["sha256"].items():
        content = (folder / f"{name}.json").read_text(encoding="utf-8")
        assert hashlib.sha256(content.encode()).hexdigest() == digest


def test_export_is_deterministic_and_keeps_money_exact(tmp_path):
    first = export_web_snapshot(export_tables(), "a", tmp_path)
    second = export_web_snapshot(export_tables(), "b", tmp_path)
    assert first["snapshot"] == second["snapshot"]

    folder = tmp_path / "snapshots" / first["snapshot"]
    segments = json.loads((folder / "customer-segments.json").read_text())
    assert {row["segment"]: row["net_revenue"] for row in segments} == {
        "At Risk": "100",
        "Core": "900",
    }
    products = json.loads((folder / "products.json").read_text())
    assert [row["product_name"] for row in products] == ["Bom", "Caro"]
    assert "maximum_discount_for_15pct_margin" not in products[0]


def test_export_replaces_the_manifest_only_at_the_end(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text('{"snapshot": "previous"}')

    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("src.analytics.web_export.Path.replace", fail)
    with pytest.raises(OSError):
        export_web_snapshot(export_tables(), "now", tmp_path)

    assert json.loads((tmp_path / "manifest.json").read_text()) == {"snapshot": "previous"}


def test_simulator_prints_json_and_disposes_the_engine(monkeypatch, capsys):
    engine = MagicMock()
    monkeypatch.setattr("sys.argv", ["simulator", "--discount", "0.18"])
    monkeypatch.setattr(simulator.Settings, "from_env", staticmethod(lambda: "settings"))
    monkeypatch.setattr(simulator, "engine_for", lambda settings: engine)
    monkeypatch.setattr(simulator, "read_fact", lambda connection: "fact")
    calls = []

    def simulate(fact, discount):
        calls.append((fact, discount))
        return {"impact": D("-1.50")}

    monkeypatch.setattr(simulator, "simulate_discount", simulate)

    simulator.main()

    assert calls == [("fact", "0.18")]
    assert json.loads(capsys.readouterr().out) == {"impact": "-1.50"}
    engine.dispose.assert_called_once()


def test_simulator_requires_a_discount(monkeypatch):
    monkeypatch.setattr("sys.argv", ["simulator"])
    with pytest.raises(SystemExit):
        simulator.main()
