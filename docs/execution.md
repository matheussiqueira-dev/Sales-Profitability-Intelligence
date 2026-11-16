# Executar do zero no Windows / PowerShell

## V2: projeto existente e camadas visíveis

Antes de atualizar um dataset V1 já gerado, preserve backup e execute na raiz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe scripts/upgrade_sources.py
.\.venv\Scripts\python.exe -m src.pipeline
```

upgrade_sources adiciona somente variable_costs.csv se ausente, sem reescrever os
sete CSVs antigos. As taxas são hipóteses sintéticas documentadas; não usar o script
para inventar custos de uma operação real. O pipeline migra schema próprio V1→V2
transacionalmente e reconcilia oito totais. Migração isolada:
`python scripts/initialize_database.py` preserva valores antigos com custo legado zero;
isso não substitui a carga da nova fonte nem evidencia custos reais nulos.

Power BI: abrir `powerbi/project/SalesProfitability.pbip`, configurar DataFolder para
a pasta absoluta data/processed deste clone, atualizar e conferir validation.md.
Modo Snapshot usa CSVs conciliados. Para conexão direta, SourceMode=PostgreSQL;
ServerName=127.0.0.1:5432 e DatabaseName do `.env`; credenciais no Desktop.
Cache/configurações locais .pbi são ignoradas. Não enviar senha no chat ou versionar.

Web: [execução](../web/README.md), http://127.0.0.1:3000.
Exportar novamente: `python scripts/export_web.py` (refaz reconciliação antes de publicar
agregados locais). Alterações requerem novo build web para renovar páginas estáticas.

O fluxo manual abaixo continua válido para um clone novo, gerando oito fontes V2.

Pré-requisitos: Git, Python 3.12+ (3.13 validado localmente), Docker Desktop iniciado.
Execute os comandos na raiz do repositório, nunca dentro de src.

```powershell
git clone https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence.git
cd Sales-Profitability-Intelligence
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

O bootstrap cria venv, instala versões fixadas, cria `.env` com segredos aleatórios
somente quando ausente, inicia PostgreSQL, aguarda healthcheck, gera dataset somente
quando ausente, executa pipeline, testes unitários e Ruff. Não sobrescreve `.env`
ou CSVs existentes, nem remove banco ou volumes. Dataset parcialmente existente
provoca erro; preserve os arquivos e configure uma pasta separada antes de continuar.
O banco full-refresh substitui apenas tabelas comprovadamente pertencentes ao projeto.

## Caminho manual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
notepad .env
```

Preencher POSTGRES_PASSWORD e PGADMIN_PASSWORD com senhas locais próprias antes de
iniciar o Compose. Não versionar `.env`. Porta padrão 5432 em loopback; se ocupada,
ajuste POSTGRES_PORT no `.env`, preservando o banco do outro projeto.
PGADMIN_EMAIL pode ser alterado para endereço local válido.

```powershell
docker compose config --quiet
docker compose up -d --wait
docker compose ps
python scripts/generate_mock_data.py
python -m src.pipeline --validate-only
python -m src.pipeline
pytest -v
ruff check .
ruff format --check .
mypy
python -m src.analytics.simulator --discount 0.18
```

`pytest` padrão pula o teste de banco; isso não prova integração. Para executá-lo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_integration.ps1
```

Esse script cria `sales_profitability_test` se ausente (exige CREATEDB) e aplica os
testes nesse banco isolado, restaurando as variáveis do processo no final. Não
usa tabelas do banco de demonstração. A carga recusa schemas estranhos e os testes
exigem nome terminando em `_test`. O banco de teste pode ser mantido para repetição.

## Fontes, amostras e determinismo

Dataset padrão: seed 42, vendas de 01/01/2024 a 31/12/2025, dados pessoais fictícios.
O gerador CLI nunca sobrescreve uma pasta que já contém CSVs. Para gerar outra base:

```powershell
python scripts/generate_mock_data.py --seed 42 --orders 40000 --output data/raw-new
```

Alterar DATA_RAW_PATH no `.env` para apontar ao novo diretório antes do pipeline.
`--seed`, `--orders`, `--customers`, `--products` configuram o gerador CLI.
O bootstrap usa RANDOM_SEED e DATA_RAW_PATH do `.env`; valores padrão são 42 e data/raw.
Para demonstração pequena, definir DATA_RAW_PATH=data/samples. As amostras são
relacionalmente completas (80 pedidos, 20 clientes, 20 produtos); não são apenas
recortes dos primeiros registros de uma base grande.

## Verificar PostgreSQL

```powershell
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

No psql:

```sql
SELECT * FROM analytics.pipeline_metadata;
SELECT * FROM analytics.vw_sales_summary;
SELECT count(*) FROM raw.order_items;
SELECT count(*) FROM staging.order_items;
SELECT count(*) FROM analytics.fact_sales;
SELECT * FROM analytics.vw_channel_profitability ORDER BY contribution_margin DESC;
\i /tmp/example.sql
```

Para arquivo SQL, copie primeiro com
`docker compose cp sql/07_example_queries.sql postgres:/tmp/example.sql`.
Alternativa sem psql: `python scripts/verify_database.py`, que grava resumo e contagens.

## PgAdmin opcional

```powershell
docker compose --profile tools up -d --wait
```

Abrir http://127.0.0.1:5050 e autenticar com PGADMIN_EMAIL/PGADMIN_PASSWORD do `.env`.
Registrar servidor: host `postgres`, porta interna `5432`, banco/usuário/senha do `.env`.
Não usar `127.0.0.1` dentro do container pgAdmin. PostgreSQL não tem página HTTP;
o dashboard Power BI é aberto no Desktop, não em URL local.

## Parar, recuperar e diagnosticar

`docker compose --profile tools down` para parar este projeto; não usar `down -v`
porque remove dados persistidos. `.env` e volumes continuam. Subir novamente preserva
o snapshot. Falha de validação/reconciliação não substitui o snapshot anterior.
Depois de falha de export, o banco pode já estar commitado: verificar completed_at,
corrigir permissões/espaço do diretório e reexecutar.

Conexão: usar POSTGRES_HOST=127.0.0.1 (evita a tentativa IPv6 de localhost no Windows).
Senha alterada no `.env` não muda senha de um volume PostgreSQL já inicializado;
restaure credencial correta ou altere a role explicitamente com backup prévio.
Não apague volumes para resolver autenticação. Erro de qualidade: consultar
`data/processed/quality-report.json`; financeiro: reconciliation.json.
O pipeline não imprime DSN nem credenciais; pode ser chamado por código para
diagnóstico local com exceções SQL parametrizadas ocultas.

Power BI: siga [guia](../powerbi/README.md). A execução remota de GitHub Actions
confirmada após o push autorizado está registrada no [relatório](history/delivery-report.md).
