# Execução adaptada V2 — 06/10/2026

Fonte de escopo: planejamento fornecido em `# Sales & Profitability Intelligenc.txt`.
Este plano preserva o MVP em 33a5624, a licença e alterações locais preexistentes.
O plano sênior paralelo permanece como referência; nesta execução, o pedido mais
recente inclui custos variáveis, Pandera e showcase web, anteriormente fora de escopo.

1. Baseline: CI remoto verde em 33a5624; rodar unitários/integração e guardar relatórios
   e backup PostgreSQL em artifacts/baseline-v1 (ignorado, sem publicar credenciais).
2. Contrato V2: taxas sintéticas de pagamento/canal/comissão sobre receita líquida,
   embalagem por item não cancelado; custo de embalagem não estornado nas devoluções.
   Simulador recalcula taxas percentuais; teto agregado pondera a base sem desconto.
3. Qualidade/warehouse: Pandera declarativo após parsing exato, relações customizadas,
   DDL explícito e migração transacional V1→V2 com teste de upgrade/rollback.
4. Decision support: oito métricas monetárias conciliadas, views, alertas e DAX V2.
5. Power BI: PBIP/TMDL/PBIR versionado, abrir no Desktop e validar dados/medidas/visuais.
   Testes de JSON/TMDL não substituem execução do DAX e captura de telas reais.
6. Web: Next.js/Tailwind/Recharts, JSONs agregados derivados de snapshot reconciliado,
   sem conexão ao banco/segredos; metodologia e identificação de dados sintéticos.
7. Release: lint/tests/build e CI atualizados, documentação com números V2 verificados.
   Não mudar visibilidade do repositório nem publicar serviços externos automaticamente.

Correções ao documento de referência: Pandera complementa o parser Decimal, sem
coerção para float. Para desconto uniforme com taxas heterogêneas, ponderar r por
`(quantity-returned_quantity)*unit_price`, não pela receita histórica descontada.
O teto é analítico antes do arredondamento; testar a margem simulada em centavos
para avaliar a política. Comissões e taxas são hipóteses do case, não benchmarks.

Fatos confirmados: repositório PRIVATE; Power BI Store 2.158.1177.0 instalado;
Docker Desktop estava parado e foi iniciado sem modificar configurações.
Não existe bundle ZIP acessível no caminho sandbox citado pelo documento;
as mudanças serão implementadas sobre o código real, sem substituir pelo skeleton.
