# Implementação no Power BI Desktop

Esta pasta entrega especificações e medidas; não contém um PBIX fabricado.
O dashboard ainda precisa ser montado e validado no Power BI Desktop.

1. Execute o pipeline e confirme os relatórios em `data/processed`.
2. Siga [Power Query](power-query.md) para importar as seis tabelas do star schema.
3. Configure [modelo e relacionamentos](../docs/data-model.md).
4. Copie as [medidas DAX](dax-measures.md), marcando a dimensão de data como calendário.
5. Monte as [cinco páginas](dashboard-specification.md).
6. Compare totais sem filtros com `analytics.vw_sales_summary`.
7. Teste filtros, drill-through, navegação por teclado e receita zero.
8. Teste o simulador em 0%, 10%, 20%, 30% e compare com Python.
9. Só então salve o PBIX e adicione screenshots reais.

Credenciais do PostgreSQL ficam no gerenciador de fontes do Desktop, nunca no código M.
Publicação no Power BI Service, gateway, RLS, licenças e refresh agendado estão fora
da entrega local. Não houve validação DAX pelo motor Power BI nesta execução.
