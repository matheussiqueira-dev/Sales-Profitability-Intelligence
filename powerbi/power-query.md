# Power Query e atualização

Modo Import. Criar parâmetros `ServerName` (Text, `127.0.0.1:5432`) e
`DatabaseName` (Text, `sales_profitability`). Usar Obter Dados → PostgreSQL,
autenticação Database com usuário/senha locais do `.env`.

Para cada tabela, criar uma consulta em branco usando o padrão M abaixo e trocar
`TableName` por `dim_date`, `dim_customer`, `dim_product`, `dim_channel`, `dim_seller`
e `fact_sales`. Dar à consulta exatamente o nome da tabela.

```powerquery
let
    TableName = "fact_sales",
    Source = PostgreSQL.Database(ServerName, DatabaseName, [CreateNavigationProperties=false]),
    TableData = Source{[Schema="analytics", Item=TableName]}[Data]
in
    TableData
```

Preservar tipos do conector: chaves e quantidades como Whole Number; dinheiro
numeric(18,2) como Fixed Decimal Number; percentuais como Decimal Number;
`full_date` como Date; `is_weekend` como True/False. Conferir manualmente cada tipo.
Não carregar raw/staging nem derivar margem novamente no Power Query.
Desabilitar Auto date/time. Remover agregação automática das chaves.

Para segmentação de clientes e metas, carregar opcionalmente
`vw_customer_profitability` e `vw_target_performance` como tabelas de apoio;
as segmentações dessas views são estáticas para o snapshot completo, sem mudança
automática sob filtros. Não relacionar views agregadas diretamente à fato com
many-to-many. O star schema é a fonte dos KPIs dinâmicos.

Após nova execução bem-sucedida do ETL: Home → Refresh → conferir data do snapshot
em `analytics.pipeline_metadata` e comparar KPIs sem filtros com a view summary.
Para Power BI Service seria necessário um gateway e configuração de credenciais.

Diagnóstico: connection refused → verificar `docker compose ps` e porta;
permission denied → verificar usuário e grants; tabelas ausentes → pipeline não
foi concluído; arredondamento → conferir Fixed Decimal Number e medidas.
