# Validação da revisão — 08/10/2026

A vitrine passou em lint, TypeScript e build de produção. Os dois testes Playwright
passaram em 1440×1000 e 390×844, verificando filtros, navegação, ausência de erros
JavaScript, overflow horizontal e headers CSP, nosniff e DENY.

Capturas da execução estão em `artifacts/web/desktop.png` e
`artifacts/web/mobile.png`; a captura mobile foi inspecionada visualmente.
Esses arquivos são evidências locais ignoradas pelo Git.

O waterfall usa uma escala comum sem ampliar artificialmente barras pequenas.
Snapshots são conferidos por hash e contrato antes da renderização. A CSP mantém
unsafe-inline para bootstrap estático e estilos dos gráficos; isso limita sua
proteção contra scripts injetados. Não há validação completa de acessibilidade.

Em 08/10 os testes Python não executaram: a política de Controle de Aplicativo
do Windows bloqueou a DLL pandas._libs.testing e o executável Ruff. Em 15/10 a
revisão foi validada: `scripts/run_container_checks.ps1` passou Ruff, formatação,
checagem de DDL e 76 testes, incluindo as 5 integrações PostgreSQL (cobertura 90%).

Power BI Desktop, refresh, paridade DAX e revisão manual das cinco páginas continuam
pendentes nesta sessão. Build web não comprova essas etapas. Nenhum deploy, commit
ou push foi realizado.
