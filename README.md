# Sales Profitability Intelligence

Uma plataforma analítica para descobrir quais produtos, clientes e canais realmente
geram rentabilidade após considerar descontos, custos, fretes e devoluções.

## Overview e problema de negócio

Faturamento alto não garante margem. Descontos agressivos, logística e devoluções
podem transformar os maiores produtos/clientes em contribuições pequenas ou negativas.
Este case deriva indicadores a partir de transações fictícias, com regras verificáveis.
Não é uma demonstração de lucro líquido nem de dados comerciais reais.

## Solução e arquitetura

CSV → Python/Pandas + qualidade → PostgreSQL RAW → STAGING → ANALYTICS → Power BI.
As três camadas são carregadas em uma transação, depois de reconciliação independente.
[Arquitetura](docs/architecture.md) · [decisões](docs/adr/001-data-architecture.md).

## Funcionalidades

- Geração determinística de 24 meses de vendas e padrões comerciais coerentes.
- Contratos e qualidade antes da escrita; nenhum descarte silencioso de duplicatas.
- Star schema, views de rentabilidade e reconciliação monetária em centavos.
- Simulador de desconto CLI e limite sustentável para meta de margem.
- Dez regras de insights com limiares e evidências, sem IA generativa.
- Docker, bootstrap PowerShell, testes unitários e integração isolada.
- Especificações de cinco páginas Power BI, Power Query e medidas DAX.

## Dataset

Base sintética padrão, seed 42, vendas entre janeiro/2024 e dezembro/2025.
Clientes/produtos/fornecedores são fictícios; localidades são brasileiras.

| CSV | Registros |
|---|---:|
| customers | 2.000 |
| products | 200 |
| orders | 40.000 |
| order_items | 101.772 |
| returns | 4.366 |
| freight | 40.000 |
| targets | 96 |

Fato: 99.235 itens de 39.002 pedidos não cancelados. Calendário: 731 dias;
quatro canais e 16 vendedores. Base completa é regenerável e ignorada pelo Git;
[amostras relacionais pequenas](data/samples) são versionadas para demonstração.

## Pipeline

`python -m src.pipeline`: ler, validar, normalizar, construir dimensões/fato, carregar
snapshot, reler valores persistidos, reconciliar e publicar exports/insights.
`--validate-only` verifica fontes sem escrever no banco. Logs não contêm credenciais.
Rerun não duplica linhas. Snapshots existentes só são atualizados em schemas próprios.

## Modelo e regras de negócio

[Star schema e relações](docs/data-model.md) · [dicionário](docs/data-dictionary.md) ·
[contrato financeiro](docs/business-rules.md).
Grão item; devoluções agregadas por item; frete proporcional à receita líquida,
com fallback por quantidade em pedido totalmente devolvido; centavos distribuídos
por maior resto. Margem % fica indefinida se receita for zero.

## Analytics e resultados reproduzidos localmente

| Indicador | Base sintética padrão |
|---|---:|
| Receita bruta | R$ 126.264.177,15 |
| Descontos | R$ 12.663.500,58 |
| Devoluções | R$ 3.605.814,43 |
| Receita líquida | R$ 109.994.862,14 |
| CMV | R$ 72.970.809,50 |
| Frete real | R$ 2.178.770,47 |
| Contribuição | R$ 34.845.282,17 |
| Margem ponderada | 31,68% |

Reconciliação passou com diferença zero nas sete métricas, IDs/contagens e frete por
pedido; SQL independente também conferiu os totais. Dez regras geraram 151 alertas
no snapshot padrão. São sinais determinísticos e não comprovação de causa.
Views por produto, cliente, canal, mês, devolução e metas;
[consultas demonstrativas](sql/07_example_queries.sql).

## Power BI Dashboard

Entregue: [guia de implementação](powerbi/README.md), [Power Query](powerbi/power-query.md),
[DAX](powerbi/dax-measures.md) e [especificação](powerbi/dashboard-specification.md).
Páginas: Executivo, Produtos, Clientes, Canais e Simulador.
PBIX, execução de DAX no motor Desktop, screenshots e validação visual permanecem
pendentes. Arquivos Markdown não são apresentados como dashboard funcionando.

## Simulador de desconto

```powershell
python -m src.analytics.simulator --discount 0.18
```

Para desconto uniforme de 18%: receita simulada R$100.264.846,94, contribuição
R$25.115.266,97, impacto −R$9.730.015,20 e crescimento de volume necessário 38,74%.
Mantém mix e taxa de devolução; compensação assume custos variáveis proporcionais.
Não é previsão de demanda. Preço=100, custos=70, margem mínima=15% → teto 17,65%.

## Data Quality

Bloqueia colunas inconsistentes, valores nulos, IDs duplicados, FKs inválidas,
preços/custos negativos, quantidades não inteiras/positivas, descontos fora de [0,1],
datas inválidas e devoluções acima da quantidade vendida. Não altera dados ruins
para “fazer passar”. Relatórios JSON registram falhas antes de tocar o banco.

## Tecnologias

Python 3.12+ (3.13.14 validado), Pandas, Decimal, SQLAlchemy, psycopg 3, PostgreSQL 17,
Docker Compose, pytest/coverage, Ruff, GitHub Actions; Power BI/Power Query/DAX como
camada de consumo especificada. [Versões fixadas](requirements.lock.txt).

## Estrutura

```text
data/samples/       amostras pequenas versionadas
data/raw/          dataset completo regenerável, ignorado
data/processed/    relatórios/exports locais, ignorados
src/config/        ambiente e conexão segura
src/ingestion/     leitura CSV
src/validation/    contratos, qualidade, reconciliação
src/transformation/ dimensões, fato e regras financeiras
src/database/      DDL, posse e carga transacional
src/analytics/     insights e simulador
sql/               modelo, views e consultas
scripts/           geração, bootstrap, verificação e dicionário
tests/             regras, qualidade, integração e rollback
powerbi/           especificação para implementação manual
docs/              arquitetura, modelo, contratos, execução, evidências
.github/workflows/ CI com testes unitários e integração PostgreSQL
```

## Executar localmente

Na raiz, com Python 3.12+, Git e Docker Desktop iniciado:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Para PgAdmin: adicionar `-WithPgAdmin`; abrir http://127.0.0.1:5050. Credenciais
locais no `.env`, nunca no Git. [Passo a passo completo](docs/execution.md).

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\ruff.exe check .
powershell -ExecutionPolicy Bypass -File scripts/run_integration.ps1
```

Integração exige banco isolado terminado em `_test`. Verifica rerun idempotente,
views, schemas desconhecidos e rollback de falha após carga. Cobertura e resultado
da última validação em [relatório de entrega](docs/delivery-report.md).
GitHub Actions passou em Linux: unitários com Python 3.12/3.13 e integração PostgreSQL.
[Execução confirmada](https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence/actions/runs/37403390421).

## Screenshots

Pendentes da construção real no Power BI Desktop. Não há imagens fictícias nem
screenshots que simulem um relatório implementado.

## Limitações e roadmap

Margem inclui CMV e frete; exclui impostos, comissões, CAC, custos fixos e perdas
de produtos devolvidos. Custo estático, sem SCD2; devolução imputada à data da venda;
full refresh local. Segmentar clientes usa o snapshot completo. Produção exige
roles de menor privilégio, TLS, backups, retenção e migrações versionadas.

Próximos passos: montar/validar PBIX → screenshots reais → revisão comercial das
premissas → política histórica de custos e devoluções → incremental/orquestração.
Aplicação web Next.js permanece expansão futura, conforme escopo confirmado.

## Autor e licença

Desenvolvido por **Matheus Siqueira** — [portfólio](https://www.matheussiqueira.dev).
Licença [MIT](LICENSE), preservada do repositório original.
