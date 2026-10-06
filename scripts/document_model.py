"""Generate exact data dictionary from owned database metadata and synthetic examples."""

import sys
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import ROOT, Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402

DESCRIPTIONS = {
    "customer_id": "ID natural do cliente sintético",
    "customer_key": "PK/FK estável do cliente",
    "customer_name": "Nome fictício; não representa pessoa/empresa real",
    "customer_type": "B2B ou B2C",
    "city": "Cidade de cadastro",
    "state": "UF brasileira",
    "region": "Região do cliente; vendedores têm região Nacional",
    "registration_date": "Data de cadastro anterior ao pedido",
    "segment": "Porte cadastral: Enterprise, Corporate, SMB, Consumer",
    "product_id": "ID natural do produto",
    "product_key": "PK/FK estável do produto",
    "product_name": "Produto fictício",
    "category": "Categoria comercial",
    "subcategory": "Linha do produto",
    "unit_cost": "Custo unitário estático, >=0",
    "list_price": "Preço de lista, maior que custo",
    "supplier": "Fornecedor fictício",
    "order_id": "ID do pedido; repete na fato por item",
    "order_date": "Data da venda",
    "channel": "Um dos quatro canais permitidos",
    "seller_id": "ID natural do vendedor",
    "status": "Estado coerente com devoluções",
    "order_item_id": "ID único do item; grão da fato",
    "quantity": "Quantidade original, inteira >0",
    "unit_price": "Preço unitário negociado, >=0",
    "discount_percentage": "Fração de desconto em [0,1], até 4 casas",
    "return_id": "ID único do evento de devolução",
    "return_date": "Data do evento >= data do pedido",
    "quantity_returned": "Quantidade no evento; soma por item <= vendida",
    "return_reason": "defective, wrong_item, customer_request, damaged ou late_delivery",
    "freight_charged": "Cobrança informativa; não compõe receita no MVP",
    "freight_actual": "Custo logístico único por pedido, >=0",
    "month": "Número do mês na dimensão; primeiro dia do mês em targets",
    "revenue_target": "Meta monetária sintética mensal/canal",
    "margin_target_percentage": "Meta de margem sintética como fração",
    "date_key": "PK/FK YYYYMMDD, data da venda",
    "full_date": "Data única do calendário contínuo",
    "day": "Dia do mês",
    "month_name": "Mês em português, ordenar pelo número",
    "quarter": "Trimestre 1–4",
    "year": "Ano civil",
    "week_of_year": "Semana ISO",
    "is_weekend": "Sábado/domingo",
    "channel_key": "PK/FK do canal, 1–4",
    "channel_name": "Nome único do canal",
    "seller_key": "PK/FK estável do vendedor",
    "seller_name": "Nome sintético do vendedor",
    "sale_key": "PK da fato igual ao order_item_id",
    "gross_revenue": "Quantidade × preço, HALF_UP centavos",
    "discount_value": "Receita bruta × desconto, HALF_UP centavos",
    "net_revenue": "Bruta − desconto − reembolso, >=0",
    "total_product_cost": "(Quantidade − devolvida) × custo, HALF_UP centavos",
    "freight_allocated": "Frete real rateado por receita; fallback quantidade",
    "returned_quantity": "Soma de unidades devolvidas do item, 0 até quantity",
    "return_value": "Reembolso proporcional à receita descontada arredondada",
    "contribution_margin": "Líquida − CMV − frete; pode ser negativa",
    "contribution_margin_percentage": "Contribuição / líquida; NULL quando líquida zero",
    "singleton": "Uma única linha true",
    "owner": "Marker de posse do warehouse",
    "contract_version": "Versão 1 do contrato; mudanças exigem migração",
    "completed_at": "Timestamp do último snapshot commitado, timezone PostgreSQL",
}


def main():
    engine = engine_for(Settings.from_env())
    lines = [
        "# Dicionário de dados",
        "",
        "Gerado de metadados PostgreSQL e exemplos sintéticos pelo script document_model.py.",
        "RAW mantém strings da origem; STAGING usa tipos e chaves dos contratos.",
        "Veja business-rules.md para arredondamento, frete, simulador e limitações.",
        "",
        "| Tabela | Campo | Tipo | Descrição / regra | Exemplo |",
        "|---|---|---|---|---|",
    ]
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            for schema in ("raw", "staging", "analytics"):
                for name in sorted(inspector.get_table_names(schema=schema)):
                    table = connection.dialect.identifier_preparer.quote_identifier(name)
                    row = (
                        connection.execute(text(f"SELECT * FROM {schema}.{table} LIMIT 1"))
                        .mappings()
                        .one_or_none()
                    )
                    pk = inspector.get_pk_constraint(name, schema=schema)["constrained_columns"]
                    for column in inspector.get_columns(name, schema=schema):
                        col = column["name"]
                        description = DESCRIPTIONS[col]
                        rule = "PK; " if col in pk else ""
                        rule += "NULL permitido; " if column["nullable"] else "NOT NULL; "
                        example = str(row[col]) if row else "sem registros"
                        if (
                            schema == "analytics"
                            and name == "pipeline_metadata"
                            and col == "completed_at"
                        ):
                            example = "timestamp do snapshot (variável)"
                        lines.append(
                            f"| {schema}.{name} | {col} | {column['type']} | "
                            f"{rule}{description} | {example.replace('|', '/')} |"
                        )
        (ROOT / "docs/data-dictionary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
