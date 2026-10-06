"""Generate PBIP model and five PBIR pages from the actual V2 warehouse contract."""

import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config.settings import ROOT, Settings  # noqa: E402
from src.database.connection import engine_for  # noqa: E402

PROJECT = ROOT / "powerbi/project"
MEASURES = {
    "Receita Bruta": "SUM(fact_sales[gross_revenue])",
    "Descontos": "SUM(fact_sales[discount_value])",
    "Devoluções": "SUM(fact_sales[return_value])",
    "Receita Líquida": "SUM(fact_sales[net_revenue])",
    "CMV": "SUM(fact_sales[total_product_cost])",
    "Frete": "SUM(fact_sales[freight_allocated])",
    "Custos Variáveis": "SUM(fact_sales[variable_cost_value])",
    "Margem": "SUM(fact_sales[contribution_margin])",
    "Margem %": "DIVIDE([Margem],[Receita Líquida])",
    "Pedidos": "DISTINCTCOUNT(fact_sales[order_id])",
    "Clientes Ativos": "DISTINCTCOUNT(fact_sales[customer_key])",
    "Ticket Médio": "DIVIDE([Receita Líquida],[Pedidos])",
    "Desconto Médio %": "DIVIDE([Descontos],[Receita Bruta])",
    "Quantidade Vendida": "SUM(fact_sales[quantity])",
    "Quantidade Devolvida": "SUM(fact_sales[returned_quantity])",
    "Taxa de Devolução": "DIVIDE([Quantidade Devolvida],[Quantidade Vendida])",
    "Desconto Selecionado": "SELECTEDVALUE('Desconto Simulado'[Value],0)",
    "Receita Simulada": (
        "SUMX(fact_sales,VAR B=ROUND((fact_sales[quantity]-fact_sales[returned_quantity])"
        "*fact_sales[unit_price]*100,0) VAR D=ROUND([Desconto Selecionado]*10000,0) "
        "VAR N=QUOTIENT(B*(10000-D)+5000,10000) RETURN CURRENCY(DIVIDE(N,100)))"
    ),
    "Custos Variáveis Simulados": (
        "SUMX(fact_sales,VAR B=ROUND((fact_sales[quantity]-fact_sales[returned_quantity])"
        "*fact_sales[unit_price]*100,0) VAR D=ROUND([Desconto Selecionado]*10000,0) "
        "VAR N=QUOTIENT(B*(10000-D)+5000,10000) "
        "VAR R=ROUND(fact_sales[variable_cost_rate]*10000,0) "
        "VAR V=QUOTIENT(N*R+5000,10000)+ROUND(fact_sales[variable_cost_fixed]*100,0) "
        "RETURN CURRENCY(DIVIDE(V,100)))"
    ),
    "Margem Simulada": "[Receita Simulada]-[CMV]-[Frete]-[Custos Variáveis Simulados]",
    "Margem Simulada %": "DIVIDE([Margem Simulada],[Receita Simulada])",
    "Impacto na Margem": "[Margem Simulada]-[Margem]",
    "Volume Necessário %": (
        "IF([Margem Simulada]>0 && [Margem]>0,DIVIDE([Margem],[Margem Simulada])-1,BLANK())"
    ),
    "Base sem Desconto": (
        "SUMX(fact_sales,(fact_sales[quantity]-fact_sales[returned_quantity])"
        "*fact_sales[unit_price])"
    ),
    "Taxa Variável Ponderada": (
        "DIVIDE(SUMX(fact_sales,(fact_sales[quantity]-fact_sales[returned_quantity])"
        "*fact_sales[unit_price]*fact_sales[variable_cost_rate]),[Base sem Desconto])"
    ),
    "Desconto Máximo para Margem 15%": (
        "VAR D=1-[Taxa Variável Ponderada]-0.15 RETURN IF([Base sem Desconto]>0 && D>0,"
        "1-DIVIDE([CMV]+[Frete]+SUM(fact_sales[variable_cost_fixed]),"
        "[Base sem Desconto]*D),BLANK())"
    ),
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def m_literal(value):
    return '"' + str(value).replace('"', '""') + '"'


def projection(table, property_name, measure=True):
    return {
        "field": {
            "Measure" if measure else "Column": {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": property_name,
            }
        },
        "queryRef": f"{table}.{property_name}",
        "nativeQueryRef": property_name,
    }


def visual(page, name, kind, x, y, width, height, roles, title):
    write(
        page / "visuals" / name / "visual.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json",
            "name": name,
            "position": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "z": 0,
                "tabOrder": y + x,
            },
            "visual": {
                "visualType": kind,
                "query": {
                    "queryState": {role: {"projections": values} for role, values in roles.items()}
                },
                "drillFilterOtherVisuals": True,
                "visualContainerObjects": {
                    "title": [
                        {
                            "properties": {
                                "show": {"expr": {"Literal": {"Value": "true"}}},
                                "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                            }
                        }
                    ]
                },
            },
        },
    )


def main():
    settings = Settings.from_env()
    engine = engine_for(settings)
    tables = []
    expressions = [
        {
            "name": "DataFolder",
            "kind": "m",
            "expression": m_literal(settings.processed_path.as_posix())
            + ' meta [IsParameterQuery=true,Type="Text",IsParameterQueryRequired=true]',
        },
        {
            "name": "ServerName",
            "kind": "m",
            "expression": m_literal(f"{settings.host}:{settings.port}")
            + ' meta [IsParameterQuery=true,Type="Text",IsParameterQueryRequired=true]',
        },
        {
            "name": "DatabaseName",
            "kind": "m",
            "expression": m_literal(settings.database)
            + ' meta [IsParameterQuery=true,Type="Text",IsParameterQueryRequired=true]',
        },
        {
            "name": "SourceMode",
            "kind": "m",
            "expression": (
                '"Snapshot" meta [IsParameterQuery=true,Type="Text",IsParameterQueryRequired=true]'
            ),
        },
    ]
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            for name in [
                "dim_date",
                "dim_customer",
                "dim_product",
                "dim_channel",
                "dim_seller",
                "fact_sales",
            ]:
                columns = []
                mtypes = []
                for col in inspector.get_columns(name, schema="analytics"):
                    dtype = str(col["type"])
                    kind = (
                        "int64"
                        if dtype == "INTEGER"
                        else "boolean"
                        if dtype == "BOOLEAN"
                        else "dateTime"
                        if dtype == "DATE"
                        else "decimal"
                        if dtype == "NUMERIC(18, 2)"
                        else "double"
                        if dtype.startswith("NUMERIC")
                        else "string"
                    )
                    mtype = {
                        "int64": "Int64.Type",
                        "boolean": "type logical",
                        "dateTime": "type date",
                        "decimal": "Currency.Type",
                        "double": "type number",
                        "string": "type text",
                    }[kind]
                    columns.append(
                        {
                            "name": col["name"],
                            "dataType": kind,
                            "sourceColumn": col["name"],
                            "summarizeBy": "none",
                        }
                    )
                    mtypes.append("{" + json.dumps(col["name"]) + "," + mtype + "}")
                query = [
                    "let",
                    (
                        f'    Csv = Csv.Document(File.Contents(DataFolder & "/{name}.csv"),'
                        '[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),'
                    ),
                    "    Headers = Table.PromoteHeaders(Csv,[PromoteAllScalars=true]),",
                    "    Snapshot = Table.TransformColumnTypes(Headers,{"
                    + ",".join(mtypes)
                    + '},"en-US"),',
                    (
                        "    PostgreSQLSource = PostgreSQL.Database(ServerName,DatabaseName,"
                        "[CreateNavigationProperties=false]),"
                    ),
                    f'    SqlTable = PostgreSQLSource{{[Schema="analytics",Item="{name}"]}}[Data],',
                    '    Result = if SourceMode = "PostgreSQL" then SqlTable else Snapshot',
                    "in Result",
                ]
                table = {
                    "name": name,
                    "columns": columns,
                    "partitions": [
                        {
                            "name": name,
                            "mode": "import",
                            "source": {"type": "m", "expression": query},
                        }
                    ],
                }
                if name == "dim_date":
                    table["columns"].append(
                        {
                            "type": "calculated",
                            "name": "year_month",
                            "dataType": "string",
                            "expression": 'FORMAT(dim_date[full_date],"yyyy-MM")',
                            "summarizeBy": "none",
                        }
                    )
                if name == "fact_sales":
                    table["measures"] = [
                        {
                            "name": measure,
                            "expression": expression,
                            "description": (
                                f"Contrato V2: {measure}. Dados sintéticos; "
                                "contribuição não é lucro líquido."
                            ),
                            "displayFolder": "Simulador"
                            if any(
                                s in measure
                                for s in (
                                    "Simulad",
                                    "Desconto Selecionado",
                                    "Máximo",
                                    "Necessário",
                                    "Ponderada",
                                    "Base sem",
                                )
                            )
                            else "Executivo",
                            "formatString": "0.00%"
                            if "%" in measure
                            or measure
                            in (
                                "Desconto Selecionado",
                                "Taxa Variável Ponderada",
                                "Desconto Máximo para Margem 15%",
                            )
                            else "#,0"
                            if measure
                            in (
                                "Pedidos",
                                "Clientes Ativos",
                                "Quantidade Vendida",
                                "Quantidade Devolvida",
                            )
                            else '"R$" #,0.00; -"R$" #,0.00',
                        }
                        for measure, expression in MEASURES.items()
                    ]
                tables.append(table)
    finally:
        engine.dispose()
    tables.append(
        {
            "name": "Desconto Simulado",
            "columns": [
                {
                    "type": "calculatedTableColumn",
                    "name": "Value",
                    "dataType": "decimal",
                    "sourceColumn": "[Value]",
                    "formatString": "0%",
                    "summarizeBy": "none",
                }
            ],
            "partitions": [
                {
                    "name": "Desconto Simulado",
                    "source": {
                        "type": "calculated",
                        "expression": "GENERATESERIES(CURRENCY(0),CURRENCY(0.30),CURRENCY(0.01))",
                    },
                }
            ],
        }
    )
    relations = [
        {
            "name": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
            "fromTable": "fact_sales",
            "fromColumn": key,
            "toTable": dim,
            "toColumn": key,
            "crossFilteringBehavior": "oneDirection",
        }
        for key, dim in [
            ("date_key", "dim_date"),
            ("customer_key", "dim_customer"),
            ("product_key", "dim_product"),
            ("channel_key", "dim_channel"),
            ("seller_key", "dim_seller"),
        ]
    ]
    model = {
        "name": "SalesProfitability",
        "compatibilityLevel": 1600,
        "model": {
            "culture": "pt-BR",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "tables": tables,
            "relationships": relations,
            "expressions": expressions,
        },
    }
    write(ROOT / "artifacts/powerbi/model.bim", model)
    write(
        PROJECT / "SalesProfitability.SemanticModel/definition.pbism",
        {"version": "4.0", "settings": {}},
    )
    write(
        PROJECT / "SalesProfitability.pbip",
        {
            "version": "1.0",
            "artifacts": [{"report": {"path": "SalesProfitability.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    report = PROJECT / "SalesProfitability.Report"
    write(
        report / "definition/version.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0",
        },
    )
    write(
        report / "definition.pbir",
        {
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../SalesProfitability.SemanticModel"}},
        },
    )
    write(
        report / "definition/report.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json",
            "themeCollection": {},
            "reportSource": "Default",
        },
    )
    pages = [
        ("executive", "Executivo"),
        ("products", "Produtos"),
        ("customers", "Clientes"),
        ("channels", "Canais"),
        ("simulator", "Simulador"),
    ]
    write(
        report / "definition/pages/pages.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [p[0] for p in pages],
            "activePageName": "executive",
        },
    )
    for page_name, display in pages:
        page = report / "definition/pages" / page_name
        write(
            page / "page.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
                "name": page_name,
                "displayName": display,
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        names = (
            ["Receita Líquida", "Margem", "Margem %", "Pedidos"]
            if page_name != "simulator"
            else ["Receita Simulada", "Margem Simulada", "Impacto na Margem", "Volume Necessário %"]
        )
        for i, measure in enumerate(names):
            visual(
                page,
                f"kpi{i}",
                "card",
                24 + i * 310,
                22,
                294,
                120,
                {"Values": [projection("fact_sales", measure)]},
                measure,
            )
        if page_name == "executive":
            visual(
                page,
                "trend",
                "lineChart",
                24,
                166,
                738,
                400,
                {
                    "Category": [projection("dim_date", "year_month", False)],
                    "Y": [
                        projection("fact_sales", "Receita Líquida"),
                        projection("fact_sales", "Margem"),
                    ],
                },
                "Receita líquida e contribuição",
            )
            visual(
                page,
                "channel",
                "clusteredBarChart",
                786,
                166,
                470,
                400,
                {
                    "Category": [projection("dim_channel", "channel_name", False)],
                    "Y": [projection("fact_sales", "Margem")],
                },
                "Contribuição por canal",
            )
        elif page_name in ("products", "customers"):
            entity = "dim_product" if page_name == "products" else "dim_customer"
            property_name = "product_name" if page_name == "products" else "customer_name"
            visual(
                page,
                "quadrant",
                "scatterChart",
                24,
                166,
                738,
                470,
                {
                    "Category": [projection(entity, property_name, False)],
                    "X": [projection("fact_sales", "Receita Líquida")],
                    "Y": [projection("fact_sales", "Margem %")],
                    "Size": [
                        projection(
                            "fact_sales",
                            "Quantidade Vendida" if page_name == "products" else "Pedidos",
                        )
                    ],
                },
                "Receita × margem",
            )
            visual(
                page,
                "matrix",
                "tableEx",
                786,
                166,
                470,
                470,
                {
                    "Values": [
                        projection(entity, property_name, False),
                        projection("fact_sales", "Receita Líquida"),
                        projection("fact_sales", "Margem"),
                        projection("fact_sales", "Margem %"),
                    ]
                },
                "Rentabilidade",
            )
        elif page_name == "channels":
            visual(
                page,
                "channel",
                "clusteredBarChart",
                24,
                166,
                738,
                470,
                {
                    "Category": [projection("dim_channel", "channel_name", False)],
                    "Y": [
                        projection("fact_sales", "Receita Líquida"),
                        projection("fact_sales", "Margem"),
                    ],
                },
                "Receita e contribuição por canal",
            )
            visual(
                page,
                "matrix",
                "tableEx",
                786,
                166,
                470,
                470,
                {
                    "Values": [
                        projection("dim_channel", "channel_name", False),
                        projection("fact_sales", "Custos Variáveis"),
                        projection("fact_sales", "Margem %"),
                    ]
                },
                "Taxas e rentabilidade",
            )
        else:
            visual(
                page,
                "discount",
                "slicer",
                24,
                166,
                450,
                180,
                {"Values": [projection("Desconto Simulado", "Value", False)]},
                "Desconto uniforme: 0–30%",
            )
            visual(
                page,
                "ceiling",
                "card",
                500,
                166,
                756,
                180,
                {"Values": [projection("fact_sales", "Desconto Máximo para Margem 15%")]},
                "Desconto máximo para meta de 15%",
            )
            visual(
                page,
                "scenarios",
                "tableEx",
                24,
                370,
                1232,
                266,
                {
                    "Values": [
                        projection("dim_channel", "channel_name", False),
                        projection("fact_sales", "Margem Simulada"),
                        projection("fact_sales", "Margem Simulada %"),
                        projection("fact_sales", "Custos Variáveis Simulados"),
                    ]
                },
                "Cenário por canal (mix e volume constantes)",
            )
    (ROOT / "powerbi/measures.dax").write_text(
        "\n\n".join(f"{name} = {value}" for name, value in MEASURES.items()) + "\n",
        encoding="utf-8",
    )
    print("PBIP model and five PBIR pages generated. Desktop validation is still required.")


if __name__ == "__main__":
    main()
