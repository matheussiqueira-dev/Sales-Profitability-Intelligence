# Relatório de entrega — 05/10/2026

Escopo confirmado: Python, PostgreSQL e especificação Power BI. Aplicação web
permanece no roadmap. Este relatório distingue código executado de tarefas manuais.

## 1. Diagnóstico inicial e arquitetura final

Repositório correto: Sales-Profitability-Intelligence, main, commit inicial 5fdb74e,
apenas licença MIT. Pasta vazia antes do clone. Nenhum código existente sobrescrito.
Arquitetura: CSV → validação/Python/Decimal → raw → staging → analytics → views,
insights, simulador e consumo Power BI. Banco local em container, persistência por
volume, sem alteração ao PostgreSQL do projeto A3 na porta 15432.

## 2. Estrutura e dataset

Pastas src/config, ingestion, transformation, validation, database, analytics;
scripts de geração, bootstrap, integração, metadados e verificação;
SQL do modelo, views e exemplos; testes; docs e powerbi.

| Origem | Linhas completas | Amostra versionada |
|---|---:|---|
| customers | 2.000 | 20 clientes |
| products | 200 | 20 produtos |
| orders | 40.000 | 80 pedidos |
| order_items | 101.772 | Todos os itens da amostra, FKs válidas |
| returns | 4.366 | Todos os eventos da amostra |
| freight | 40.000 | 80 pedidos |
| targets | 96 | 96 metas |

Seed 42; 24 meses, quatro canais, seis categorias, cinco regiões brasileiras e
16 vendedores na base completa. Nomes fictícios. Padrões: sazonalidade, desconto
agressivo nos grandes clientes, maior frete/menor margem no marketplace e produtos
de baixa contribuição. Valores não são evidência de negócio real.

## 3. Pipeline, banco e modelo

`python -m src.pipeline` executou no PostgreSQL 17.11 com sucesso. raw/staging têm
as sete fontes completas; analytics tem 731 datas, 2.000 clientes, 200 produtos,
quatro canais, 16 vendedores e 99.235 itens de 39.002 pedidos não cancelados.
PKs/FKs/checks/índices reais. Marker de posse/versão, advisory lock e carga atomicamente
revertida em falhas. Rerun repetível testado, sem duplicação. Dados persistiram após
parar/subir os containers sem remover volumes.

## 4. Regras financeiras e qualidade

Decimal HALF_UP em centavos; receita bruta, descontos, reembolso proporcional ao
valor descontado arredondado, receita líquida, CMV retido e contribuição pós-frete.
Frete por receita líquida com fallback por quantidade e maior resto para centavos.
Margem % NULL se receita zero. Contrato e limitações em business-rules.md.

Qualidade bloqueia campos/IDs nulos, duplicatas, FKs, números/ranges/datas inválidos,
quantidades não inteiras, devoluções acumuladas excessivas, estados inconsistentes
e falta de frete. Não descarta dados silenciosamente. Base completa passou sem erros.

| Reconciliação | Origem = warehouse | Diferença |
|---|---:|---:|
| Receita bruta | 126.264.177,15 | 0,00 |
| Descontos | 12.663.500,58 | 0,00 |
| Devoluções | 3.605.814,43 | 0,00 |
| Receita líquida | 109.994.862,14 | 0,00 |
| CMV | 72.970.809,50 | 0,00 |
| Frete | 2.178.770,47 | 0,00 |
| Contribuição | 34.845.282,17 | 0,00 |

IDs/contagem da fato e frete por pedido também reconciliados. SQL independente
recalculou receita bruta, desconto, reembolso e CMV de staging. Margem ponderada 31,68%.

## 5. SQL, testes e ferramentas

Sete views: summary, produto, cliente, canal, mês, devolução e metas. Quatro consultas
demonstrativas executadas: top produtos (10), top clientes (10), produtos alta
receita/baixa margem (12) e tetos de desconto (200). Não há consulta não validada
apresentada como resultado.

Última suíte completa: **59 testes passaram**, via scripts/run_integration.ps1,
incluindo banco isolado sales_profitability_test. Cobertura medida em src: **92%**
(475/518 statements), funções financeiras **100%**. CLI foi executada manualmente;
seu wrapper não foi incluído na cobertura de testes. Ruff check e format-check passam.
pip check passou. Imports reais pelo pipeline e testes; compileall também verificado.

Testes incluem os dez casos financeiros do texto, dados inválidos, devolução acumulada,
rateio, centavos, limite sustentável, simulador, reconciliação corrompida, carga repetida,
recusa de tabelas desconhecidas e rollback após falha financeira. Testes em 3.12/Linux
estão configurados no CI, mas não foram executados remotamente nesta entrega.

Falhas encontradas e resolvidas: tentativa localhost/IPv6 no Windows (host loopback
explícito + timeout); Pandas inferindo Decimal como VARCHAR (tipos PostgreSQL
refletidos no loader); domínio reservado do exemplo PgAdmin (endereço válido);
passagem de Python inline com aspas pelo PowerShell 5 (scripts Python próprios).
Não houve carga parcial aceita durante esses erros.

## 6. Power BI, simulador e insights

Entregue documentação de Power Query, star schema, medidas DAX, cinco páginas,
simulador What-if 0–30% com passo 1%, segmentação e checklist visual/teclado/mobile.
Skill senior-ui-polish lida e considerada na especificação; não existe interface web
ou PBIX para polir/verificar nesta execução. **PBIX, DAX no Desktop e visual QA pendentes**.

Algoritmo de teto sustentável implementado/testado em Python e SQL; exemplo
preço=100, custo=63, frete=7, meta=15% → desconto máximo 17,6470588%.
Simulador CLI executado em 18%: receita 100.264.846,94; contribuição 25.115.266,97;
margem 25,0489%; impacto −9.730.015,20; crescimento compensatório 38,7414%.
Premissas explícitas, sem previsão de demanda. Dez regras determinísticas produzindo
151 alertas no snapshot completo, com limiares e evidências registrados.

## 7. Documentação, execução e Git

README orientado ao problema, arquitetura, modelo, dicionário gerado do PostgreSQL,
contrato financeiro, dois ADRs, execução PowerShell, plano inicial e este relatório.
Bootstrap preserva `.env`, CSVs e volumes; validações e scripts não enviam push.
GitHub Actions configurada com testes unitários 3.12/3.13 e PostgreSQL isolado.
Não há resultado remoto de CI antes de autorização de push.

Bootstrap completo executado via PowerShell, após restart do Compose sem remoção
de volumes: pipeline passou, 58 testes unitários passaram (integração fora desse
comando), Ruff passou e hashes de `.env`/order_items.csv preservados.
Verificação de banco executada novamente, com mesmos totais e contagens.
Links locais da documentação conferidos, sem links quebrados.

Commits foram separados por estrutura, dataset/configuração, SQL, pipeline/testes,
Power BI/docs e automação/validação. Branch main; situação final e hashes estão no
resumo de Git fornecido ao usuário. O relatório não promete publicação remota.

Nenhum segredo real foi versionado: `.env` ignorado, exemplos sem senha,
scan por credenciais locais no conteúdo versionado sem ocorrência. A senha fixa
de CI é exclusivamente de serviço efêmero de teste, declarada via ambiente;
não corresponde a conta real. Logs e URL ocultam senha/parâmetros.

## 8. Pendências e próximos passos

1. Autorização explícita para git push; nenhuma publicação realizada.
2. Executar workflow no GitHub e observar resultados reais.
3. Montar/validar Power BI Desktop e salvar PBIX/screenhots reais.
4. Revisar com negócio os limites do MVP: impostos/comissões/CAC/custos fixos,
   devoluções recuperáveis, custo estático e competência da data de venda.
5. Para produção: roles de menor privilégio, TLS, backup/restauração, migrações,
   incremental e política de atualização. Aplicação web segue roadmap.

Quality gates locais de ambiente, geração, Docker/PostgreSQL, três camadas, dimensões,
fato, reconciliação, testes, Ruff, documentação e Git foram executados. Aprovação
de publicação, dashboard real e operação produtiva permanecem separados.
