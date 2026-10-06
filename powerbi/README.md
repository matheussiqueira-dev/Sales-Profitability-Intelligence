# Implementação no Power BI Desktop

## Projeto V2 executado

Abrir [SalesProfitability.pbip](project/SalesProfitability.pbip). Existem cinco páginas
PBIR e modelo TMDL; carregado e salvo no Desktop Store 2.158.1177.0.
Oito totais e quatro cenários foram executados no DAX e conciliados com Python/SQL:
[evidência](validation.md). Medidas vigentes em [measures.dax](measures.dax).
O projeto permite Snapshot/CSV e PostgreSQL via SourceMode; não versiona senha/cache.
Snapshot CSV já foi executado. Autenticação e refresh direto PostgreSQL são um gate
separado; consulte o relatório V2 para o estado atual dessa verificação.

As instruções seguintes foram escritas para montagem manual V1 e ficam como contexto;
para a implementação vigente prevalecem projeto e validação V2.

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
