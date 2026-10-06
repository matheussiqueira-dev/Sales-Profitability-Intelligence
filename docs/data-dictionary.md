# Dicionário de dados

Gerado de metadados PostgreSQL e exemplos sintéticos pelo script document_model.py.
RAW mantém strings da origem; STAGING usa tipos e chaves dos contratos.
Veja business-rules.md para arredondamento, frete, simulador e limitações.

| Tabela | Campo | Tipo | Descrição / regra | Exemplo |
|---|---|---|---|---|
| raw.customers | customer_id | VARCHAR | PK; NOT NULL; ID natural do cliente sintético | 1 |
| raw.customers | customer_name | VARCHAR | NOT NULL; Nome fictício; não representa pessoa/empresa real | Cliente Sintético 0001 |
| raw.customers | customer_type | VARCHAR | NOT NULL; B2B ou B2C | B2B |
| raw.customers | city | VARCHAR | NOT NULL; Cidade de cadastro | São Paulo |
| raw.customers | state | VARCHAR | NOT NULL; UF brasileira | SP |
| raw.customers | region | VARCHAR | NOT NULL; Região do cliente; vendedores têm região Nacional | Sudeste |
| raw.customers | registration_date | VARCHAR | NOT NULL; Data de cadastro anterior ao pedido | 2023-10-17 |
| raw.customers | segment | VARCHAR | NOT NULL; Porte cadastral: Enterprise, Corporate, SMB, Consumer | Enterprise |
| raw.freight | order_id | VARCHAR | PK; NOT NULL; ID do pedido; repete na fato por item | 1 |
| raw.freight | freight_charged | VARCHAR | NOT NULL; Cobrança informativa; não compõe receita no MVP | 29.21 |
| raw.freight | freight_actual | VARCHAR | NOT NULL; Custo logístico único por pedido, >=0 | 48.68 |
| raw.order_items | order_item_id | VARCHAR | PK; NOT NULL; ID único do item; grão da fato | 1 |
| raw.order_items | order_id | VARCHAR | NOT NULL; ID do pedido; repete na fato por item | 1 |
| raw.order_items | product_id | VARCHAR | NOT NULL; ID natural do produto | 40 |
| raw.order_items | quantity | VARCHAR | NOT NULL; Quantidade original, inteira >0 | 3 |
| raw.order_items | unit_price | VARCHAR | NOT NULL; Preço unitário negociado, >=0 | 374.69 |
| raw.order_items | discount_percentage | VARCHAR | NOT NULL; Fração de desconto em [0,1], até 4 casas | 0.00 |
| raw.orders | order_id | VARCHAR | PK; NOT NULL; ID do pedido; repete na fato por item | 1 |
| raw.orders | order_date | VARCHAR | NOT NULL; Data da venda | 2024-01-01 |
| raw.orders | customer_id | VARCHAR | NOT NULL; ID natural do cliente sintético | 1057 |
| raw.orders | channel | VARCHAR | NOT NULL; Um dos quatro canais permitidos | Loja Física |
| raw.orders | seller_id | VARCHAR | NOT NULL; ID natural do vendedor | 6 |
| raw.orders | status | VARCHAR | NOT NULL; Estado coerente com devoluções | partially_returned |
| raw.products | product_id | VARCHAR | PK; NOT NULL; ID natural do produto | 1 |
| raw.products | product_name | VARCHAR | NOT NULL; Produto fictício | Eletrônicos Produto 001 |
| raw.products | category | VARCHAR | NOT NULL; Categoria comercial | Eletrônicos |
| raw.products | subcategory | VARCHAR | NOT NULL; Linha do produto | Linha 2 |
| raw.products | unit_cost | VARCHAR | NOT NULL; Custo unitário estático, >=0 | 550.85 |
| raw.products | list_price | VARCHAR | NOT NULL; Preço de lista, maior que custo | 1001.54 |
| raw.products | supplier | VARCHAR | NOT NULL; Fornecedor fictício | Fornecedor Sintético 02 |
| raw.returns | return_id | VARCHAR | PK; NOT NULL; ID único do evento de devolução | 1 |
| raw.returns | order_item_id | VARCHAR | NOT NULL; ID único do item; grão da fato | 3 |
| raw.returns | return_date | VARCHAR | NOT NULL; Data do evento >= data do pedido | 2024-01-18 |
| raw.returns | quantity_returned | VARCHAR | NOT NULL; Quantidade no evento; soma por item <= vendida | 2 |
| raw.returns | return_reason | VARCHAR | NOT NULL; defective, wrong_item, customer_request, damaged ou late_delivery | damaged |
| raw.targets | month | VARCHAR | PK; NOT NULL; Número do mês na dimensão; primeiro dia do mês em targets | 2024-01-01 |
| raw.targets | channel | VARCHAR | PK; NOT NULL; Um dos quatro canais permitidos | Loja Física |
| raw.targets | revenue_target | VARCHAR | NOT NULL; Meta monetária sintética mensal/canal | 500000.00 |
| raw.targets | margin_target_percentage | VARCHAR | NOT NULL; Meta de margem sintética como fração | 0.20 |
| staging.customers | customer_id | INTEGER | PK; NOT NULL; ID natural do cliente sintético | 1 |
| staging.customers | customer_name | VARCHAR | NOT NULL; Nome fictício; não representa pessoa/empresa real | Cliente Sintético 0001 |
| staging.customers | customer_type | VARCHAR | NOT NULL; B2B ou B2C | B2B |
| staging.customers | city | VARCHAR | NOT NULL; Cidade de cadastro | São Paulo |
| staging.customers | state | VARCHAR | NOT NULL; UF brasileira | SP |
| staging.customers | region | VARCHAR | NOT NULL; Região do cliente; vendedores têm região Nacional | Sudeste |
| staging.customers | registration_date | DATE | NOT NULL; Data de cadastro anterior ao pedido | 2023-10-17 |
| staging.customers | segment | VARCHAR | NOT NULL; Porte cadastral: Enterprise, Corporate, SMB, Consumer | Enterprise |
| staging.freight | order_id | INTEGER | PK; NOT NULL; ID do pedido; repete na fato por item | 1 |
| staging.freight | freight_charged | NUMERIC(18, 2) | NOT NULL; Cobrança informativa; não compõe receita no MVP | 29.21 |
| staging.freight | freight_actual | NUMERIC(18, 2) | NOT NULL; Custo logístico único por pedido, >=0 | 48.68 |
| staging.order_items | order_item_id | INTEGER | PK; NOT NULL; ID único do item; grão da fato | 1 |
| staging.order_items | order_id | INTEGER | NOT NULL; ID do pedido; repete na fato por item | 1 |
| staging.order_items | product_id | INTEGER | NOT NULL; ID natural do produto | 40 |
| staging.order_items | quantity | INTEGER | NOT NULL; Quantidade original, inteira >0 | 3 |
| staging.order_items | unit_price | NUMERIC(18, 2) | NOT NULL; Preço unitário negociado, >=0 | 374.69 |
| staging.order_items | discount_percentage | NUMERIC(8, 4) | NOT NULL; Fração de desconto em [0,1], até 4 casas | 0.0000 |
| staging.orders | order_id | INTEGER | PK; NOT NULL; ID do pedido; repete na fato por item | 1 |
| staging.orders | order_date | DATE | NOT NULL; Data da venda | 2024-01-01 |
| staging.orders | customer_id | INTEGER | NOT NULL; ID natural do cliente sintético | 1057 |
| staging.orders | channel | VARCHAR | NOT NULL; Um dos quatro canais permitidos | Loja Física |
| staging.orders | seller_id | INTEGER | NOT NULL; ID natural do vendedor | 6 |
| staging.orders | status | VARCHAR | NOT NULL; Estado coerente com devoluções | partially_returned |
| staging.products | product_id | INTEGER | PK; NOT NULL; ID natural do produto | 1 |
| staging.products | product_name | VARCHAR | NOT NULL; Produto fictício | Eletrônicos Produto 001 |
| staging.products | category | VARCHAR | NOT NULL; Categoria comercial | Eletrônicos |
| staging.products | subcategory | VARCHAR | NOT NULL; Linha do produto | Linha 2 |
| staging.products | unit_cost | NUMERIC(18, 2) | NOT NULL; Custo unitário estático, >=0 | 550.85 |
| staging.products | list_price | NUMERIC(18, 2) | NOT NULL; Preço de lista, maior que custo | 1001.54 |
| staging.products | supplier | VARCHAR | NOT NULL; Fornecedor fictício | Fornecedor Sintético 02 |
| staging.returns | return_id | INTEGER | PK; NOT NULL; ID único do evento de devolução | 1 |
| staging.returns | order_item_id | INTEGER | NOT NULL; ID único do item; grão da fato | 3 |
| staging.returns | return_date | DATE | NOT NULL; Data do evento >= data do pedido | 2024-01-18 |
| staging.returns | quantity_returned | INTEGER | NOT NULL; Quantidade no evento; soma por item <= vendida | 2 |
| staging.returns | return_reason | VARCHAR | NOT NULL; defective, wrong_item, customer_request, damaged ou late_delivery | damaged |
| staging.targets | month | DATE | PK; NOT NULL; Número do mês na dimensão; primeiro dia do mês em targets | 2024-01-01 |
| staging.targets | channel | VARCHAR | PK; NOT NULL; Um dos quatro canais permitidos | Loja Física |
| staging.targets | revenue_target | NUMERIC(18, 2) | NOT NULL; Meta monetária sintética mensal/canal | 500000.00 |
| staging.targets | margin_target_percentage | NUMERIC(8, 4) | NOT NULL; Meta de margem sintética como fração | 0.2000 |
| analytics.dim_channel | channel_key | INTEGER | PK; NOT NULL; PK/FK do canal, 1–4 | 1 |
| analytics.dim_channel | channel_name | TEXT | NOT NULL; Nome único do canal | Loja Física |
| analytics.dim_customer | customer_key | INTEGER | PK; NOT NULL; PK/FK estável do cliente | 1 |
| analytics.dim_customer | customer_id | INTEGER | NOT NULL; ID natural do cliente sintético | 1 |
| analytics.dim_customer | customer_name | TEXT | NOT NULL; Nome fictício; não representa pessoa/empresa real | Cliente Sintético 0001 |
| analytics.dim_customer | customer_type | TEXT | NOT NULL; B2B ou B2C | B2B |
| analytics.dim_customer | segment | TEXT | NOT NULL; Porte cadastral: Enterprise, Corporate, SMB, Consumer | Enterprise |
| analytics.dim_customer | city | TEXT | NOT NULL; Cidade de cadastro | São Paulo |
| analytics.dim_customer | state | TEXT | NOT NULL; UF brasileira | SP |
| analytics.dim_customer | region | TEXT | NOT NULL; Região do cliente; vendedores têm região Nacional | Sudeste |
| analytics.dim_date | date_key | INTEGER | PK; NOT NULL; PK/FK YYYYMMDD, data da venda | 20240101 |
| analytics.dim_date | full_date | DATE | NOT NULL; Data única do calendário contínuo | 2024-01-01 |
| analytics.dim_date | day | INTEGER | NOT NULL; Dia do mês | 1 |
| analytics.dim_date | month | INTEGER | NOT NULL; Número do mês na dimensão; primeiro dia do mês em targets | 1 |
| analytics.dim_date | month_name | TEXT | NOT NULL; Mês em português, ordenar pelo número | Janeiro |
| analytics.dim_date | quarter | INTEGER | NOT NULL; Trimestre 1–4 | 1 |
| analytics.dim_date | year | INTEGER | NOT NULL; Ano civil | 2024 |
| analytics.dim_date | week_of_year | INTEGER | NOT NULL; Semana ISO | 1 |
| analytics.dim_date | is_weekend | BOOLEAN | NOT NULL; Sábado/domingo | False |
| analytics.dim_product | product_key | INTEGER | PK; NOT NULL; PK/FK estável do produto | 1 |
| analytics.dim_product | product_id | INTEGER | NOT NULL; ID natural do produto | 1 |
| analytics.dim_product | product_name | TEXT | NOT NULL; Produto fictício | Eletrônicos Produto 001 |
| analytics.dim_product | category | TEXT | NOT NULL; Categoria comercial | Eletrônicos |
| analytics.dim_product | subcategory | TEXT | NOT NULL; Linha do produto | Linha 2 |
| analytics.dim_product | supplier | TEXT | NOT NULL; Fornecedor fictício | Fornecedor Sintético 02 |
| analytics.dim_seller | seller_key | INTEGER | PK; NOT NULL; PK/FK estável do vendedor | 1 |
| analytics.dim_seller | seller_id | INTEGER | NOT NULL; ID natural do vendedor | 1 |
| analytics.dim_seller | seller_name | TEXT | NOT NULL; Nome sintético do vendedor | Vendedor Sintético 01 |
| analytics.dim_seller | region | TEXT | NOT NULL; Região do cliente; vendedores têm região Nacional | Nacional |
| analytics.fact_sales | sale_key | INTEGER | PK; NOT NULL; PK da fato igual ao order_item_id | 1 |
| analytics.fact_sales | order_id | INTEGER | NOT NULL; ID do pedido; repete na fato por item | 1 |
| analytics.fact_sales | order_item_id | INTEGER | NOT NULL; ID único do item; grão da fato | 1 |
| analytics.fact_sales | date_key | INTEGER | NOT NULL; PK/FK YYYYMMDD, data da venda | 20240101 |
| analytics.fact_sales | customer_key | INTEGER | NOT NULL; PK/FK estável do cliente | 1057 |
| analytics.fact_sales | product_key | INTEGER | NOT NULL; PK/FK estável do produto | 40 |
| analytics.fact_sales | channel_key | INTEGER | NOT NULL; PK/FK do canal, 1–4 | 1 |
| analytics.fact_sales | seller_key | INTEGER | NOT NULL; PK/FK estável do vendedor | 6 |
| analytics.fact_sales | quantity | INTEGER | NOT NULL; Quantidade original, inteira >0 | 3 |
| analytics.fact_sales | unit_price | NUMERIC(18, 2) | NOT NULL; Preço unitário negociado, >=0 | 374.69 |
| analytics.fact_sales | gross_revenue | NUMERIC(18, 2) | NOT NULL; Quantidade × preço, HALF_UP centavos | 1124.07 |
| analytics.fact_sales | discount_percentage | NUMERIC(8, 4) | NOT NULL; Fração de desconto em [0,1], até 4 casas | 0.0000 |
| analytics.fact_sales | discount_value | NUMERIC(18, 2) | NOT NULL; Receita bruta × desconto, HALF_UP centavos | 0.00 |
| analytics.fact_sales | net_revenue | NUMERIC(18, 2) | NOT NULL; Bruta − desconto − reembolso, >=0 | 1124.07 |
| analytics.fact_sales | unit_cost | NUMERIC(18, 2) | NOT NULL; Custo unitário estático, >=0 | 318.49 |
| analytics.fact_sales | total_product_cost | NUMERIC(18, 2) | NOT NULL; (Quantidade − devolvida) × custo, HALF_UP centavos | 955.47 |
| analytics.fact_sales | freight_allocated | NUMERIC(18, 2) | NOT NULL; Frete real rateado por receita; fallback quantidade | 29.30 |
| analytics.fact_sales | returned_quantity | INTEGER | NOT NULL; Soma de unidades devolvidas do item, 0 até quantity | 0 |
| analytics.fact_sales | return_value | NUMERIC(18, 2) | NOT NULL; Reembolso proporcional à receita descontada arredondada | 0.00 |
| analytics.fact_sales | contribution_margin | NUMERIC(18, 2) | NOT NULL; Líquida − CMV − frete; pode ser negativa | 139.30 |
| analytics.fact_sales | contribution_margin_percentage | NUMERIC(20, 10) | NULL permitido; Contribuição / líquida; NULL quando líquida zero | 0.1239246666 |
| analytics.pipeline_metadata | singleton | BOOLEAN | PK; NOT NULL; Uma única linha true | True |
| analytics.pipeline_metadata | owner | TEXT | NOT NULL; Marker de posse do warehouse | sales-profitability-intelligence |
| analytics.pipeline_metadata | contract_version | INTEGER | NOT NULL; Versão 1 do contrato; mudanças exigem migração | 1 |
| analytics.pipeline_metadata | completed_at | TIMESTAMP | NULL permitido; Timestamp do último snapshot commitado, timezone PostgreSQL | timestamp do snapshot (variável) |
