# Plano e diagnóstico inicial

Em 05/10/2026, o remoto confirmado foi
`https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence.git`.
Branch inicial `main`, commit `5fdb74e`, apenas LICENSE MIT, sem código ou configurações.
A pasta local estava vazia antes do clone. Nenhum arquivo existente foi sobrescrito.
Python 3.13.14 e Docker Engine 29.8.0 disponíveis; PostgreSQL de outro projeto usa
15432 e não será alterado.

Sequência: estrutura → ambiente/configuração/Docker → geração sintética → qualidade
→ SQL/modelo → ETL/reconciliação → consultas/testes/lint → documentação Power BI
→ simulador/insights → documentação/execução/CI → validação final/commits.
Cada incremento terá verificação real. Não haverá push sem autorização explícita.

O texto de execução é a especificação principal. A aplicação web sugerida pelo
briefing é expansão de roadmap. PBIX e validação visual no Power BI Desktop são
entregas manuais, sem arquivos falsos. A licença MIT existente permanece.

Decisões financeiras: seguir as fórmulas do texto de execução; frete cobrado é
informativo, sem compor receita líquida; devolução recupera CMV integralmente;
custos operacionais adicionais e impostos não entram na margem do MVP.
Marketplace terá frete/logística maiores; comissões ficam como limitação explícita.
