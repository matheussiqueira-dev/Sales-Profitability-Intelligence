from decimal import Decimal

import pandas as pd
from sqlalchemy import text


def generate_insights(tables):
    """Return actionable signals with measured evidence and explicit thresholds."""
    summary = tables["sales_summary"].iloc[0]
    products, customers = tables["product_profitability"], tables["customer_profitability"]
    channels, months = tables["channel_profitability"], tables["monthly_performance"]
    alerts = []
    evaluated = []

    def rule(name):
        evaluated.append(name)

    def alert(name, entity, message, evidence):
        alerts.append(
            {
                "rule": name,
                "entity": str(entity),
                "message": message,
                "evidence": {k: str(v) for k, v in evidence.items()},
            }
        )

    rule("revenue_up_margin_down")
    months = months.sort_values("month")
    for previous, current in zip(
        months.iloc[:-1].itertuples(), months.iloc[1:].itertuples(), strict=True
    ):
        if current.net_revenue > previous.net_revenue and (
            current.margin_percentage is not None
            and previous.margin_percentage is not None
            and current.margin_percentage < previous.margin_percentage
        ):
            alert(
                "revenue_up_margin_down",
                current.month,
                "Receita cresceu e margem percentual caiu. Investigue desconto, custos e mix; "
                "o sinal não estabelece causalidade.",
                {
                    "revenue_change": current.net_revenue / previous.net_revenue - 1,
                    "margin_change_pp": (current.margin_percentage - previous.margin_percentage)
                    * 100,
                },
            )

    rule("customer_revenue_margin_concentration")
    if summary.net_revenue > 0 and summary.contribution_margin > 0:
        for row in customers.itertuples():
            revenue_share = row.net_revenue / summary.net_revenue
            margin_share = row.contribution_margin / summary.contribution_margin
            if revenue_share >= Decimal(".005") and margin_share < revenue_share / 2:
                alert(
                    "customer_revenue_margin_concentration",
                    row.customer_name,
                    "Cliente representa >=0,5% da receita e menos da metade dessa participação "
                    "na margem. Reveja condições comerciais.",
                    {"revenue_share": revenue_share, "margin_share": margin_share},
                )

    rule("product_high_returns")
    for row in products.itertuples():
        if row.quantity >= 30 and row.return_rate > summary.return_rate * 2:
            alert(
                "product_high_returns",
                row.product_name,
                "Devoluções excedem 2x a taxa ponderada do portfólio (mínimo 30 unidades).",
                {"return_rate": row.return_rate, "baseline": summary.return_rate},
            )

    rule("channel_low_margin")
    for row in channels.itertuples():
        if row.margin_percentage is not None and row.margin_percentage < summary.margin_percentage:
            alert(
                "channel_low_margin",
                row.channel_name,
                "Margem do canal está abaixo da margem ponderada do portfólio.",
                {"margin_percentage": row.margin_percentage, "baseline": summary.margin_percentage},
            )

    rule("negative_product_margin")
    for row in products.itertuples():
        if row.contribution_margin < 0:
            alert(
                "negative_product_margin",
                row.product_name,
                "Produto tem contribuição negativa. Investigue preço, frete e devoluções.",
                {"margin": row.contribution_margin},
            )

    rule("high_discount_customers")
    for row in customers.itertuples():
        if row.discount_percentage > Decimal(".20"):
            alert(
                "high_discount_customers",
                row.customer_name,
                "Desconto ponderado por receita bruta excede 20%.",
                {"discount_percentage": row.discount_percentage},
            )

    rule("high_freight_channels")
    for row in channels.itertuples():
        if row.net_revenue > 0 and row.freight_allocated / row.net_revenue > Decimal(".05"):
            alert(
                "high_freight_channels",
                row.channel_name,
                "Frete supera 5% da receita líquida. Avalie logística e política de cobrança.",
                {"freight_share": row.freight_allocated / row.net_revenue},
            )

    rule("unsafe_discount_products")
    for row in products.itertuples():
        ceiling = row.maximum_discount_for_15pct_margin
        if ceiling is not None and ceiling < 0:
            alert(
                "unsafe_discount_products",
                row.product_name,
                "Mesmo sem desconto, a meta de margem de 15% não é atingível no mix observado.",
                {"maximum_discount": ceiling},
            )

    rule("customer_at_risk")
    for row in customers.itertuples():
        if row.profitability_segment == "At Risk":
            alert(
                "customer_at_risk",
                row.customer_name,
                "Cliente sem pedido há mais de 90 dias em relação à última venda da base.",
                {"last_order_date": row.last_order_date},
            )

    rule("revenue_target_missed")
    for row in tables["target_performance"].itertuples():
        if row.revenue_attainment is not None and row.revenue_attainment < Decimal(".80"):
            alert(
                "revenue_target_missed",
                f"{row.month}/{row.channel}",
                "Receita abaixo de 80% da meta sintética mensal.",
                {"attainment": row.revenue_attainment},
            )
    return {"rules_evaluated": evaluated, "alerts_count": len(alerts), "alerts": alerts}


def read_analytics(connection):
    names = [
        "sales_summary",
        "product_profitability",
        "customer_profitability",
        "channel_profitability",
        "monthly_performance",
        "return_analysis",
        "target_performance",
    ]
    return {
        name: pd.read_sql(
            text(f"SELECT * FROM analytics.vw_{name}"), connection, coerce_float=False
        )
        for name in names
    }
