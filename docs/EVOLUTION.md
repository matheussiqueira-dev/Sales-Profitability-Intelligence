# Plano de Evolução — Sales-Profitability-Intelligence

> Documento vivo, revisado semanalmente. Última revisão: 2026-10-23.
> Regra central: nenhuma mudança entra sem estar ligada a um objetivo desta página e sem manter ou melhorar as métricas da seção 2.

## 1. Identidade do projeto

- **Propósito:** case de Dados e BI que mostra quanto da receita sobrevive a descontos, devoluções, CMV, frete e taxas (margem de contribuição) por produto, cliente e canal, com trilha completa do número: gerador sintético → contratos Pandera → PostgreSQL raw/staging/analytics → reconciliação Python × SQL × DAX → Power BI (PBIP/TMDL) e vitrine Next.js que lê só snapshots agregados conferidos por SHA-256.
- **Tipo:** pipeline de dados + warehouse + modelo Power BI + web app estático de vitrine.
- **Stack:**
  - Python ≥ 3.12 (CI em 3.12 e 3.13): pandas 3.0.6, Pandera 0.34.1, SQLAlchemy 2.1.3, psycopg 3.3.6, python-dotenv 1.2.4, jsonschema 4.26.0; pytest 9.1.1, pytest-cov 7.1.0, Ruff 0.16.10 (`requirements.lock.txt`);
  - PostgreSQL 17 (`postgres:17-alpine` com digest) e pgAdmin 9 opcional (Docker Compose);
  - Power BI PBIP com páginas PBIR e modelo TMDL em `powerbi/project/`;
  - `web/`: Next.js 16.4.0, React 19.3.0, Recharts 3, Tailwind CSS 4.3.3, TypeScript 5.9.3, ESLint 9.39.5 + `eslint-config-next` 16.4.0, Playwright 1.63.0, Prettier 3.9.9; Node 22 no CI.
- **Gerenciador de pacotes:** pip com `requirements.lock.txt` (pins exatos; `requirements.txt` com faixas) e npm (`web/package-lock.json`, ranges com `^` no `package.json`).
- **Deploy:** Vercel, projeto `inteligence-bi`, Root Directory `web`; produção em https://inteligence-bi-tau.vercel.app (README, `docs/web-release.md`). Repositório privado.
- **Estrutura:**
  - `src/` — `ingestion`, `validation` (Pandera, qualidade, reconciliação), `transformation` (dimensões, vendas, métricas financeiras), `database` (conexão, loader, lease de sessão), `analytics` (insights, simulador, publicação recuperável, export web), `pipeline.py`;
  - `sql/` — DDL e views analíticas; `scripts/` — gerador de dados, DDL, Power BI, export web, checagens;
  - `tests/` — 12 arquivos (unitários e 5 de integração PostgreSQL marcados `integration`);
  - `powerbi/` — projeto PBIP e documentação DAX/Power Query; `docs/` — arquitetura, ADRs 001–006, dicionário, relatórios de entrega e revisão;
  - `web/` — `app/` (`/` e `/methodology`), `components/`, `lib/` (validação do manifesto e formatação), `public/data/snapshots/` (dois snapshots), `tests/showcase.spec.ts`;
  - raiz com arquivos de briefing e rascunhos (`Sales Profitability Intelligence briefing.md`/`.pdf`, `# Sales & Profitability Intelligenc.txt`, `search.txt`).
- **Comandos:** install `pip install -r requirements.lock.txt` · `cd web && npm ci` · dev `npm run dev` · lint `ruff check . && ruff format --check .` · `npm run lint` · typecheck `npm run typecheck` (Python sem typecheck) · test `pytest -m 'not integration'` / `RUN_DB_TESTS=1 pytest --cov=src` (PostgreSQL isolado) / `npx playwright test` · build `npm run build`; pipeline `python -m src.pipeline`.

## 2. Estado atual (baseline)

| Verificação | Comando | Resultado | Data |
| --- | --- | --- | --- |
| Instalação | `python3.12 -m venv .venv && pip install -r requirements.lock.txt` · `npm ci` (Node 22.22.0) | PASS · PASS (419 pacotes) | 2026-10-23 |
| Lint | `ruff check .` · `ruff format --check .` · `npm run lint` | PASS · PASS (83 arquivos) · PASS | 2026-10-23 |
| Typecheck | `npm run typecheck` | PASS; Python sem mypy/pyright | 2026-10-23 |
| Testes | `pytest -m 'not integration' -q` | 71 passando / 0 falhando / 5 de integração não executados (sem PostgreSQL: daemon Docker indisponível) | 2026-10-23 |
| Cobertura | `pytest -m 'not integration' --cov=src` | 67% só com unitários (`simulator.py` 0%, `insights.py` 8%, `lease.py` 22%, `web_export.py` 24%, `loader.py` 27%, `pipeline.py` 46%); com integração: não verificado (README declara 90%) | 2026-10-23 |
| Checagens de dados | `generate_source_ddl.py --check` · gerador smoke (80 pedidos) · `verify_powerbi.py` | PASS · PASS · PASS (`desktop_dax_validation: false`; validação DAX exige Power BI Desktop) | 2026-10-23 |
| Testes e2e | `npx playwright test` | não verificado (depende do build e de navegador indisponível no ambiente) | 2026-10-23 |
| Build | `npm run build` | não verificado: FAIL por ambiente — `next/font/google` (Source Serif 4, Source Sans 3) sem acesso a `fonts.googleapis.com` | 2026-10-23 |
| Vulnerabilidades (audit) | `pip-audit -r requirements.lock.txt` · `npm audit --omit=dev` · `npm audit` | Python 0 · web runtime **1 critical** (`next` 16.4.0; corrigido em 16.4.3) · web completa 1 critical / 1 high (`zod` via `eslint-config-next`) | 2026-10-23 |
| CI no GitHub | `gh run list` | 5 jobs (`unit` 3.12/3.13, `integration` com PostgreSQL, `web`, `powerbi-artifacts` em Windows); últimas 4 execuções verdes, a mais recente em 2026-10-16 | 2026-10-23 |

Observações:
- O job `web` roda `npm audit --omit=dev` sem `--audit-level`, então o critical do `next` 16.4.0 deixa o próximo run vermelho. O range `^16.0.0` permite 16.4.3 só com atualização do lockfile.
- Continuam versionados (`git ls-files`): `Sales Profitability Intelligence briefing.md`, `Sales Profitability Intelligence briefing.pdf`, `# Sales & Profitability Intelligenc.txt`, `search.txt` e `docs/business-model-visual-prompt.txt` — rascunhos de planejamento e conversa que não são produto. Com o repositório privado, o risco é de exposição se ele for tornado público.
- Já resolvido desde a auditoria de 2026-10-11: trabalho local de 08/10 commitado (publicação recuperável, ponte financeira, headers de segurança, ADR-006), `.cto-toolkit/` fora do índice e no `.gitignore`.
- Pendentes da mesma auditoria e confirmados no código: `robots: { index: false, follow: false }` (`web/app/layout.tsx:24`), footer fora do padrão A.9, ausência de `web/tests/parity.spec.ts`, Playwright sem `channel`, `web/package.json` sem scripts `test`/`format`, tema claro e fontes Source fora do padrão dark-only/IBM Plex Sans (`docs/web-design.md`).
- O README mistura V1 e V2: "Contribuição R$ 34.845.282,17 / margem 31,68%" (V1) ao lado de "R$ 25.104.575,63 / 22,82%" (V2) e três contagens de testes diferentes (69, 71, 76).

## 3. Histórico e trajetória

- **Fase 1 — MVP V1 (2026-10-05, 11 commits):** estrutura, dataset determinístico (seed 42), warehouse PostgreSQL com views analíticas, pipeline validado e testes financeiros, scripts Windows endurecidos, CI com integração PostgreSQL isolada e checagem de credenciais.
- **Fase 2 — V2 (2026-10-06, 9 commits):** contrato financeiro com custos variáveis, migração do warehouse, vitrine Next.js conciliada, projeto Power BI validado no Desktop com cenários DAX exatos, digests de imagens fixados, publicação na Vercel com smoke remoto e CI V2 verde.
- **Fase 3 — revisão de arquitetura (2026-10-16, 7 commits):** publicação recuperável com lease de sessão no warehouse (ADR-006), redesign da ponte financeira com headers de segurança, revisão de 2026-10-08 registrada, canvas de modelo de negócio e runbook do Power BI, Playwright em porta dedicada, `.cto-toolkit` fora do índice.
- **Churn (últimos 50 commits):** `README.md` (7), `.gitignore` (6), `web/playwright.config.ts`, `src/pipeline.py` e `ci.yml` (4 cada). O README é reescrito a cada fase e acumula números de versões diferentes.
- **Padrões:** Conventional Commits com escopo; documentação extensa (21 arquivos em `docs/`, vários relatórios de entrega sobrepostos). Débitos: cobertura unitária baixa nos módulos de saída (insights, simulador, export), teste web com valor fixo ("22,8%"), arquivos de rascunho na raiz.

## 4. Objetivos definidos (critério de parada)

| # | Eixo | Objetivo | Métrica | Baseline | Meta | Prioridade | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O1 | Funcionamento | Os 5 jobs do CI verdes e produção com headers completos | jobs verdes; `/` e `/methodology` 200 com CSP, `nosniff`, `Referrer-Policy`, `Permissions-Policy` | job `web` previsto vermelho (critical); produção não verificada | 5/5 por 4 semanas; headers presentes | P0 | ativo |
| O2 | Cobertura de testes | Cobrir os módulos de saída sem depender do banco | cobertura unitária de `src/` · menor módulo de `analytics/` | 67% · 0% (`simulator.py`) | ≥ 85% · ≥ 70% | P2 | ativo |
| O3 | Segurança/Higiene | Nenhum rascunho ou conversa versionado; 0 critical/high | arquivos de rascunho no índice · `npm audit` critical+high | 5 · 2 | 0 · 0 | P0 | ativo |
| O4 | Performance | Lighthouse mobile da vitrine registrado | Perf / A11y / BP / SEO em `/` | não medido | ≥ 90 / ≥ 95 / ≥ 95 / ≥ 90 | P2 | ativo |
| O5 | Qualidade/Manutenibilidade | Uma versão dos números e da documentação | conjuntos de KPIs diferentes no README · relatórios de entrega ativos | 2 (V1 e V2) · 5 relatórios sobrepostos | 1 (V2) · 1 + histórico arquivado | P1 | ativo |
| O6 | Dados | Paridade comprovada entre UI e snapshot | `parity.spec.ts` (8 degraus da ponte + 5 KPIs) · valores fixos em teste | ausente · 1 ("22,8%") | verde, em centavos · 0 | P1 | ativo |

## 5. Guardrails

- Mudança só com objetivo associado (O#) ou item de backlog (B#); refatoração sem ganho mensurável é proibida.
- Nenhuma métrica da seção 2 pode piorar; se piorar, a mudança é revertida.
- Upgrade de versão major, mudança de arquitetura, remoção de funcionalidade e alteração de deploy exigem aprovação do dono (entram em "Decisões pendentes").
- No máximo uma feature nova por semana, de risco baixo, atrás de testes.
- Snapshots em `web/public/data/` só mudam pelo pipeline (`scripts/export_web.py` / `python -m src.analytics.publication`), nunca à mão; o build falha se o SHA-256 divergir.
- `powerbi/project/**` só muda por `scripts/generate_powerbi.py` com `scripts/verify_powerbi.py` verde.
- Digests de imagem em `docker-compose.yml` e `ci.yml` não mudam sem revisão; a credencial `ephemeral_ci_only` não é reutilizada fora do CI.
- Valores monetários seguem como decimal/centavos (sem coerção para float); toda mudança de regra financeira passa pela reconciliação Python × SQL × DAX.
- Repositório privado: nenhum link de código na UI ou no README até decisão do dono; arquivos de rascunho saem do índice só com aprovação.

## 6. Backlog priorizado

- P0 = quebra funcionamento/segurança · P1 = risco alto · P2 = qualidade · P3 = melhoria

- [ ] **B1 (P0, O1/O3)** Atualizar `next` e `eslint-config-next` para 16.4.3 no lockfile (e `zod` transitivo) — `npm audit` sem critical/high; job `web` verde com lint, typecheck, build e Playwright.
- [ ] **B2 (P0, O3)** Retirar do índice os 5 arquivos de rascunho com `git rm --cached` (cópia local preservada, com aprovação) e ignorá-los — `git ls-files` sem eles; decisão sobre purga de histórico registrada antes de tornar o repositório público.
- [ ] **B3 (P1, O6)** Criar `web/tests/parity.spec.ts` lendo o `executive-summary.json` do snapshot ativo — 8 degraus da ponte, 5 KPIs e canais batem em centavos; nenhum percentual fixo nos testes; trocar snapshot não exige editar teste.
- [ ] **B4 (P1, O5)** Reescrever o README com um único conjunto de números (V2) e uma contagem de testes medida, arquivando os relatórios V1/V2 em `docs/history/` — README cita o run de CI e não contradiz o código.
- [ ] **B5 (P1, O1)** Smoke de produção registrado — `/` e `/methodology` 200, rota inexistente 404, headers completos, sem `X-Powered-By`; anotado na seção 10.
- [ ] **B6 (P2, O2)** Testes unitários de `simulator.py`, `insights.py` e `web_export.py` com fixtures pequenas — cada um ≥ 70%; total unitário ≥ 85%.
- [ ] **B7 (P2, O1)** Fontes via `next/font/local` (Source ou IBM Plex conforme decisão de design) — `npm run build` passa sem acesso a `fonts.googleapis.com`.
- [ ] **B8 (P2, O5)** Scripts `test:e2e` e `format:check` no `web/package.json` (Prettier já instalado) e `channel` configurável no Playwright — CI chama os scripts; `prettier --check` com 0.
- [ ] **B9 (P2, O1)** Alinhar o shell ao padrão: footer A.9 sem link para o repositório privado, favicon PI, `metadataBase` e OG — favicon 200; footer visível em `/` e `/methodology`.
- [ ] **B10 (P2, O4)** Lighthouse mobile e axe da vitrine registrados — axe 0 serious/critical em 320/768/1280 px; números na seção 10.
- [ ] **B11 (P2, O5)** mypy no código Python (`src/`) com config versionada — 0 erros no job `unit`.
- [ ] **B12 (P3, O5)** Atualizar actions para as majors atuais, fixar por SHA e Node 24 no job `web` — workflow sem `@v4`/`@v5` soltos; CI verde.

## 7. Radar técnico

| Data | Item | Fonte | Veredito (adotar / avaliar / descartar) | Motivo |
| --- | --- | --- | --- | --- |
| 2026-10-23 | Next.js 16.4.3 (RCE no Image Optimization e em `use cache`, DoS em Server Actions) | https://github.com/advisories/GHSA-2464-fhr4-w9xw | adotar | Critical no runtime; quebra o job `web`. |
| 2026-10-23 | `next/font/local` para self-host explícito | https://nextjs.org/docs/app/api-reference/components/font | adotar | Build reprodutível sem rede; mesmo resultado em produção. |
| 2026-10-23 | Power BI Projects (PBIP/PBIR/TMDL) | https://learn.microsoft.com/power-bi/developer/projects/projects-overview | avaliar | Acompanhar mudanças do formato PBIR que afetem `generate_powerbi.py` e `verify_tmdl.ps1`. |
| 2026-10-23 | ESLint 9 fora de suporte | https://eslint.org/version-support | adotar (com aprovação) | Migrar para 10 junto com o config do Next. |
| 2026-10-23 | Playwright 1.64.1 | https://playwright.dev/docs/release-notes | adotar | Patch; o lock está em 1.63.0. |
| 2026-10-23 | Node 24 LTS no CI e na Vercel | https://nodejs.org/en/about/previous-releases | avaliar | CI usa Node 22; alinhar com os demais repositórios do portfólio. |

## 8. Ideias de features

| # | Feature | Valor para o usuário/portfólio | Risco | Status (proposta / aprovada / implementada / descartada) |
| --- | --- | --- | --- | --- |
| F1 | Simulador de desconto na web (reuso das regras do CLI sobre o snapshot) | Mostra a decisão comercial na vitrine; demonstra paridade entre Python e TypeScript | médio (exige fixtures de paridade) | proposta |
| F2 | Filtros coordenados (canal × categoria × período) na ponte financeira | Exploração do "onde a margem se perde"; demonstra estado de filtro na URL | baixo | proposta |
| F3 | Página de linhagem do número (CSV → raw → staging → analytics → snapshot) com hashes | Trilha auditável visível para quem avalia Dados/BI | baixo | proposta |
| F4 | Download do snapshot agregado em CSV com hash | Reuso e verificação externa | baixo | proposta |
| F5 | Painel de insights (as 10 regras) com evidência e limiar | Expõe a camada de regras hoje só em CLI | médio (cobertura de `insights.py` em 8%) | proposta |

## 9. Decisões pendentes do dono

- Produto canônico: este repositório ou `Intelig-ncia-de-vendas-e-rentabilidade`?
- Design: adotar o padrão dark-only, IBM Plex Sans e `ms-tokens.css`, ou manter a exceção de `docs/web-design.md` (tema claro, Source Serif/Sans)?
- Retirar os arquivos de rascunho do índice agora? O repositório será público (exige purga de histórico)?
- Indexar a vitrine (`robots` hoje `noindex`)?
- Alias legível na Vercel (ex.: `sales-profitability-intelligence.vercel.app`) mantendo o domínio atual?
- Manter o snapshot `14454a47e6ebbaab` (não referenciado pelo manifesto) por causa da política de recuperação do ADR-006?

## 10. Registro semanal

| Data | Auditoria | Mudanças (commits) | Métricas | Próximo foco |
| --- | --- | --- | --- | --- |
| 2026-10-23 | Documento inicial e baseline | — | ver seção 2 | B1, B2 (O1/O3) |
