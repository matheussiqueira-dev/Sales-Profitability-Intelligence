# Plano de evolução para entrega sênior

Data: 06/10/2026 · Base avaliada: `main` em `33a5624` · Substitui o
[plano inicial](implementation-plan.md) como plano vigente; aquele permanece como
registro histórico do MVP.

Objetivo: levar o projeto de "MVP local bem testado" para uma entrega que um
avaliador técnico (analytics engineer, BI lead, hiring manager) reconheça como
sênior em até cinco minutos de leitura e uma execução reprodutível.

## 0. Base de pesquisa (verificada)

Pesquisa multi-fonte com verificação adversarial (3 votos por afirmação). Só entram
aqui afirmações confirmadas, ou conferidas depois na documentação oficial. As
referências estão em [Fontes](#7-fontes).

| Tema | O que a fonte sustenta | Consequência no plano |
|---|---|---|
| Power BI como código | Um PBIP grava as definições do relatório e do modelo semântico como arquivos de texto em pastas separadas (`.Report`, `.SemanticModel`), prontos para Git e CI/CD [1] | Fase 1 entrega PBIP no lugar de PBIX binário |
| TMDL | Em TMDL, a pasta `definition\` substitui o `model.bim`, com um arquivo por tabela, role, perspectiva e cultura, o que facilita diff e merge. Exige `definition.pbism` ≥ 4.0 [2] | Revisão de medidas DAX vira revisão de código |
| Edição externa | O TMDL pode ser editado no VS Code ou no Tabular Editor; o Desktop detecta a mudança e pede confirmação antes de aplicar [1] | Best Practice Analyzer roda sobre os arquivos do repositório |
| dbt: contratos e testes | Um contrato garante a *forma* do modelo (colunas, tipos e, no Postgres, as constraints not_null, PK, FK, unique e check). Um data test verifica o *conteúdo* depois do build [3] | O projeto já faz os dois em Python/SQL. Migrar só se o grafo de linhagem e a documentação compensarem (ADR) |
| dbt: testes unitários | Indicados para lógica complexa e para modelos críticos; devem rodar só em dev/CI [4] | Se adotar dbt, testar `vw_customer_profitability` (CASE com percentis) |
| SQLMesh | A comparação publicada pelo próprio SQLMesh é tendenciosa. Uma afirmação dessa página foi **refutada** na verificação [5] | Não basear a escolha de ferramenta em material do fornecedor |
| Frescor | Uma checagem de frescor falha quando a última materialização é mais antiga que o limite configurado, o que torna o SLA testável [6] | Fase 3: frescor consultável e verificado, mesmo sem orquestrador |
| Orquestração | No Dagster 1.8, `AutomationCondition` substituiu `AutoMaterializePolicy` [7] | Se a Fase 5 adotar Dagster, usar a API atual |
| RLS/roles | Superusuários e roles com BYPASSRLS sempre ignoram RLS. O dono da tabela também ignora, salvo com `FORCE ROW LEVEL SECURITY`. Sem policy, vale default-deny [8] | Fase 3: o leitor do Power BI não pode ser dono das tabelas |
| Lockfile | `uv sync --locked` falha se o `uv.lock` estiver desatualizado; `uv lock --check` faz a mesma verificação de forma isolada [9] | Fase 0: portão de reprodutibilidade no CI |

Lacunas da pesquisa: estas afirmações não foram verificadas porque a execução
atingiu o limite: OpenLineage, `pip-audit` como action e os efeitos da fusão
Fivetran/dbt Labs/Tobiko sobre o dbt-core. A pesquisa também não trouxe evidência
verificada sobre o que recrutadores avaliam em portfólio. As recomendações de
apresentação (Fase 6) vêm da avaliação do código, não de fonte externa.

## 1. Diagnóstico com evidência

Medições feitas nesta avaliação (Windows, Python 3.13.14, sem Docker ativo):

| Verificação | Resultado |
|---|---|
| `pytest -m "not integration"` | 58 passaram |
| Cobertura **só unitária** em `src` | **67%** (insights 8%, loader 25%, simulator 0%, pipeline 49%) |
| Cobertura com integração (relatório de entrega) | 92% — depende do PostgreSQL |
| `ruff check` / `ruff format --check` | passam |
| Funções em `src` sem tipo de retorno | 31 de 33 |
| Dashboard Power BI | só especificação Markdown; sem PBIX/PBIP, sem screenshots |

### O que já sinaliza senioridade (preservar)

- Dinheiro em `Decimal`/`numeric(18,2)`, HALF_UP, rateio de frete por maior resto
  com soma exata por pedido — e testes dos casos de borda.
- Reconciliação independente (Python + SQL) com tolerância zero antes do commit;
  carga atômica, advisory lock, marcador de posse, rollback testado.
- Qualidade que bloqueia em vez de "consertar" dados; relatórios JSON.
- Honestidade documental: limitações e pendências explícitas, nada fabricado.
- CI com matriz 3.12/3.13 e integração PostgreSQL efêmera.

### Lacunas que um avaliador sênior notaria (ordenadas por impacto)

1. **Não há produto analítico visível.** É um case de BI sem dashboard. O
   avaliador não consegue ver o resultado sem montar o Power BI à mão.
2. **Cobertura real depende de banco.** Regras de insight, loader e simulador
   quase não têm teste unitário; não há limite mínimo de cobertura no CI.
3. **Tipagem ausente** em quase todo `src` e sem verificador estático no CI.
4. **Evolução de schema bloqueada.** `contract_version CHECK (= 1)` e
   `CREATE ... IF NOT EXISTS` não têm caminho de migração.
5. **Execução sem histórico.** `pipeline_metadata` é singleton; não há
   `run_id`, histórico de execuções, contagens por camada, duração ou
   frescor consultáveis. Raw é sobrescrito a cada carga.
6. **Uma única role de banco** (bootstrap) para DDL, carga e leitura; o Power BI
   usaria a mesma credencial.
7. **Cadeia de suprimentos do CI frouxa:** actions por tag, lockfile sem hashes,
   dependências de teste/lint dentro das dependências de runtime do pacote
   (`requirements.txt` → `pyproject` dynamic), sem auditoria de vulnerabilidades,
   sem lint de SQL, sem `pre-commit`.
8. **Execução só PowerShell.** CI roda Linux, mas o caminho documentado é
   Windows; falta um ponto de entrada multiplataforma (`make`/`just`/`tasks`).
9. **Insights pouco acionáveis:** 151 alertas sem ranking por impacto financeiro.
   Um gestor não lê 151 alertas.
10. **Narrativa de negócio diluída.** README mistura resultado, processo e
    evidência; `delivery-report.md` é log de processo. Falta "3 achados + decisão
    recomendada" e uma seção de trade-offs.
11. Pequenos defeitos de modelo: `0.85` fixo em `vw_product_profitability`
    (meta de 15% embutida na view); `discount_value` sem `CHECK >= 0`;
    import local em `reconcile_sql` para evitar ciclo.

## 2. Princípios do plano

- Cada fase termina com evidência verificável (comando, CI verde, screenshot real).
- Nenhuma ferramenta entra sem ADR curto com alternativa rejeitada.
- Preservar o que já é forte: regras financeiras em Python/Decimal continuam a
  fonte da verdade; não reescrever o que está correto para "usar ferramenta X".
- Fora de escopo deliberado: aplicação Next.js, Airflow/Kubernetes, nuvem paga,
  PBIX "fabricado" sem validação no Desktop.

## 3. Fases

Estimativas para uma pessoa, em dias úteis focados.

### Fase 0 — Higiene e baseline (0,5 dia)

| Entrega | Critério de aceite |
|---|---|
| Separar dependências: runtime em `[project.dependencies]`; `pytest`, `pytest-cov`, `ruff`, `mypy` em `[project.optional-dependencies].dev` (ou `[dependency-groups]`) | `pip install .` não instala pytest/ruff |
| Migrar para `uv` com `uv.lock` (alternativa: `pip-compile --generate-hashes`) | CI roda `uv lock --check` e `uv sync --locked`; lock desatualizado falha o build |
| `.pre-commit-config.yaml`: ruff, ruff-format, end-of-file, check-yaml, detect-private-key | `pre-commit run --all-files` passa |
| Corrigir defeitos do item 11 (meta de margem parametrizada, CHECK de desconto) | testes de integração cobrem a view |

### Fase 1 — Produto visível: Power BI como código (3–4 dias) — **maior retorno**

| Entrega | Critério de aceite |
|---|---|
| Relatório montado no Desktop e salvo em **PBIP** (modelo semântico em TMDL + relatório em PBIR), versionado em `powerbi/project/` | diff legível no Git; abre no Desktop a partir do clone |
| Conexão parametrizada (host/porta/banco como parâmetros M); credencial só no Desktop | nenhum segredo no repositório (scan) |
| Medidas DAX da especificação no modelo, com pasta de exibição, descrições e formatos | Best Practice Analyzer (Tabular Editor) sem erros; regras ignoradas justificadas |
| Teste de paridade: totais do Power BI = `vw_sales_summary` (sete métricas) e simulador 0/10/20/30% = Python | tabela de evidência em `powerbi/validation.md` com números reais |
| Screenshots reais das cinco páginas + GIF curto do simulador em `docs/images/` | README mostra a página executiva acima da dobra |
| Opcional: publicação "Publish to web" (dados 100% sintéticos) ou PDF exportado | link público funcionando; aviso de dados fictícios |

### Fase 2 — Confiabilidade de engenharia (2–3 dias)

| Entrega | Critério de aceite |
|---|---|
| Tipagem completa de `src` + `mypy --strict` (ou pyright strict) no CI | zero erros; `Any` só em fronteiras pandas documentadas |
| Testes unitários para as dez regras de insight, loader (`read_statements`, `initialize` com connection fake/SQLite onde aplicável) e CLI do simulador | cobertura **unitária** ≥ 85%; `--cov-fail-under` no CI |
| Testes baseados em propriedade (Hypothesis) para `allocate_freight` e `financial_metrics` | invariantes: soma exata, não negatividade, idempotência |
| CI endurecido: actions fixadas por SHA, `concurrency`, `timeout-minutes`, Dependabot (pip + actions), `pip-audit`, `sqlfluff lint sql/` (dialeto postgres) | todos os jobs verdes; badge no README |
| Ponto de entrada multiplataforma (`Makefile` ou `justfile`) espelhando `setup.ps1` | `make setup && make test` em Linux/macOS; PowerShell preservado |

### Fase 3 — Operação do warehouse (2–3 dias)

| Entrega | Critério de aceite |
|---|---|
| Migrações versionadas (Alembic com SQL explícito, ou tabela `schema_migrations` + arquivos numerados) — ADR 003 | banco v1 existente migra para v2 sem perda; teste de integração cobre upgrade |
| `analytics.pipeline_runs`: `run_id`, início/fim, status, hashes das fontes, contagens raw/staging/fato, resultado da reconciliação, versão do código (git SHA) | `pipeline_metadata` vira view do último run com sucesso |
| Colunas de linhagem em raw (`_run_id`, `_loaded_at`, `_source_file`) | consulta liga cada linha da fato ao arquivo e run de origem |
| Logs estruturados (JSON) com `run_id`; duração por etapa | log de execução anexado como artefato no CI |
| Roles de menor privilégio: `sales_owner` (DDL/migrações), `sales_loader` (DML em raw/staging/analytics), `sales_reader` (SELECT só em `analytics`) — script idempotente | Power BI conecta com `sales_reader`; teste prova que reader não escreve; `sales_reader` não é dono, superusuário nem BYPASSRLS (pré-requisito para RLS futura) |
| Verificação de frescor: view/consulta com idade do último snapshot | Power BI exibe "dados de dd/mm hh:mm" |

### Fase 4 — Profundidade analítica (2 dias)

| Entrega | Critério de aceite |
|---|---|
| Ranking de alertas por impacto financeiro estimado (R$ de contribuição em risco), severidade e top-N por regra | `insights.json` com `impact_brl`, `severity`; página do Power BI mostra top 10 |
| Documento "Achados e recomendações": 3 achados principais, magnitude, decisão sugerida, limitações | linkado no topo do README |
| Catálogo de métricas único (nome, fórmula, grão, dono, onde está em Python/SQL/DAX) | teste verifica que toda métrica do catálogo existe nas três camadas |
| Sensibilidade do simulador por canal/categoria (não só desconto uniforme) | resultados reconciliam com Python |

### Fase 5 — Escala e histórico (opcional, 3–5 dias)

Somente depois das fases 1–4. Cada item exige ADR.

- Fato de devoluções por data de devolução (alternativa já prevista no ADR 002).
- Custo de produto como SCD2 (`valid_from`/`valid_to`) e fato usando custo vigente.
- Carga incremental por partição de mês com reconciliação por partição.
- Benchmark com 1M itens: vetorizar validação/fato onde o perfil indicar;
  registrar tempo e memória antes/depois.
- Avaliar dbt-core para a camada de views (testes, docs e grafo de linhagem)
  mantendo regras monetárias em Python — decidir por ADR, não por moda.
- Orquestração leve (Dagster/Prefect) só se houver agendamento real.

### Fase 6 — Apresentação (0,5–1 dia)

| Entrega | Critério de aceite |
|---|---|
| README reestruturado: problema → screenshot → 3 achados → arquitetura (diagrama) → como rodar em 1 comando → decisões e trade-offs → limitações | leitura em ≤ 5 min; links funcionando (verificador de links no CI) |
| Resumo em inglês no topo (ou `README.en.md`) | mesmo conteúdo essencial |
| `delivery-report.md` movido para `docs/history/`; changelog/tags semânticas (`v0.1.0` MVP, `v0.2.0` Power BI…) | releases no GitHub com notas |
| ADRs novos: 003 migrações, 004 roles, 005 Power BI como código, 006 decisão sobre dbt | formato contexto/decisão/alternativas/consequências |

## 4. Sequência e marcos

```text
F0 higiene ─► F1 Power BI (PBIP + screenshots) ─► F2 confiabilidade ─► F3 operação
                                                     │
                                                     └─► F4 analítica ─► F6 apresentação
F5 (opcional) só após F4
```

| Marco | Contém | Tag |
|---|---|---|
| M1 "visível" | F0 + F1 | `v0.2.0` |
| M2 "confiável" | F2 + F3 | `v0.3.0` |
| M3 "decisão" | F4 + F6 | `v1.0.0` |

Total estimado das fases obrigatórias: 10–14 dias focados.

## 5. Riscos

| Risco | Mitigação |
|---|---|
| Power BI Desktop só em Windows; PBIP/TMDL depende de recursos em preview na versão instalada | registrar versão do Desktop; manter especificação Markdown como fallback |
| Migrar para ferramentas novas quebrar a reconciliação | reconciliação continua portão obrigatório em todo PR |
| Escopo crescer (web app, nuvem) | fora de escopo explícito; só via ADR |
| Cobertura inflada por testes superficiais | exigir asserts de valor; Hypothesis para invariantes |

## 6. Definição de pronto (por PR)

- `ruff`, formatação, `mypy`, `sqlfluff`, testes unitários e integração verdes no CI.
- Reconciliação com diferença zero no dataset padrão.
- Documentação e números do README atualizados a partir de execução real.
- Nenhum segredo, `.env` ou dado real versionado.

## 7. Fontes

1. Microsoft Learn — [Power BI Desktop projects (PBIP)](https://learn.microsoft.com/power-bi/developer/projects/projects-overview)
2. Microsoft Learn — [Semantic model folder (TMDL)](https://learn.microsoft.com/power-bi/developer/projects/projects-dataset)
3. dbt Docs — [Model contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts)
4. dbt Docs — [Unit tests](https://docs.getdbt.com/docs/build/unit-tests)
5. SQLMesh — [Comparisons](https://sqlmesh.readthedocs.io/en/latest/comparisons/) (fonte do fornecedor)
6. Dagster Docs — [Checking for data freshness](https://docs.dagster.io/concepts/assets/asset-checks/checking-for-data-freshness)
7. Dagster Blog — [Dagster 1.8](https://dagster.io/blog/dagster-1-8-call-me-maybe)
8. PostgreSQL 17 — [Row Security Policies](https://www.postgresql.org/docs/17/ddl-rowsecurity.html)
9. uv Docs — [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
