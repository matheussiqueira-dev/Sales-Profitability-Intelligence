# Contrato financeiro

Grão: um item de pedido não cancelado. Cancelados permanecem em raw/staging,
mas não entram nos KPIs. Quantidade inclui unidades devolvidas; quantidade retida
é vendida menos devolvida. Vendas integralmente devolvidas permanecem na fato,
com receita/CMV zero e possível contribuição negativa pelo frete.

Todas as entradas monetárias são centavos exatos. Python usa Decimal;
PostgreSQL numeric(18,2). Arredondamento HALF_UP em cada operação monetária.
Percentuais são frações: 0.15 = 15%; nunca 15. Não há margem pré-calculada na origem.

| Métrica | Fórmula |
|---|---|
| Receita bruta G | quantidade × preço unitário, arredondado |
| Desconto D | round(G × desconto, 2) |
| Reembolso R | round((G − D) × quantidade devolvida / quantidade, 2) |
| Receita líquida N | G − D − R |
| CMV C | round((quantidade − devolvida) × custo unitário, 2) |
| Contribuição M | N − C − frete alocado |
| Margem % | M / N; NULL/BLANK se N = 0 |
| Ticket | soma N / pedidos distintos não cancelados |
| Desconto médio % | soma D / soma G |
| Taxa devolução | unidades devolvidas / unidades vendidas |

O reembolso é proporcional ao valor descontado já arredondado: a fórmula equivale
à fórmula do briefing antes de arredondar, mas garante restituição exata em devolução
integral (ex.: 3 × R$0,05 com 10% desconto: G=0,15, D=0,02, reembolso=0,13).
Múltiplos eventos de devolução são somados por item antes de calcular reembolso.
A quantidade acumulada nunca pode superar a vendida. Retornos são atribuídos à data
da venda na fato; `return_date` fica em staging. Este modelo não reproduz contabilização
de eventos de devolução em períodos posteriores.

Frete real: proporcional à receita líquida dos itens do pedido. Quando soma N=0,
ratear pela quantidade original. Arredondar para baixo em centavos e distribuir
centavos restantes pelas maiores frações, desempate pelo `order_item_id` crescente.
Soma do rateio deve coincidir exatamente com frete real do pedido. Frete cobrado
é informativo e não entra na receita líquida. Cancelados têm frete sintético zero.

CMV devolvido é integralmente recuperado; avarias, perdas, comissões, impostos,
custos fixos e CAC não são modelados. A contribuição não representa lucro líquido.
Custo de produto é estático na base; projeto não é histórico SCD2 de preços/custos.

## Desconto sustentável e simulação

Com preço P>0, custo C, frete/custo variável V e margem mínima m em [0,1):
`d_max = 1 - (C+V)/(P*(1-m))`. Deriva de
`(P*(1-d)-C-V)/(P*(1-d)) >= m`.
P=100, C=63, V=7, m=0,15 → 17,6470588%. Limite negativo indica meta impossível
mesmo sem desconto. Não confundir margem percentual sobre receita com markup sobre custo.

Simulador substitui descontos históricos por desconto uniforme 0–30%, preserva mix,
unidades retidas e custos; receita simulada de cada linha é arredondada diretamente.
Contribuição simulada = receita simulada − CMV − frete.
Fator de volume = contribuição atual / contribuição simulada; crescimento = fator−1.
Só calculável se ambas contribuições forem positivas. Compensação pressupõe todos
os custos variáveis (inclusive frete) crescendo proporcionalmente ao volume.
Não modela elasticidade, capacidade, estoque ou custos fixos.

## Regras de insights

| Regra | Limiar / evidência |
|---|---|
| revenue_up_margin_down | Receita sobe e margem % cai contra mês observado anterior |
| customer_revenue_margin_concentration | Receita share >=0,5%; margem share < metade do share de receita |
| product_high_returns | >=30 unidades e devolução >2× taxa ponderada do portfólio |
| channel_low_margin | Margem % abaixo da margem ponderada global |
| negative_product_margin | Contribuição absoluta negativa |
| high_discount_customers | Desconto ponderado >20% |
| high_freight_channels | Frete / receita líquida >5% |
| unsafe_discount_products | Limite para meta 15% negativo |
| customer_at_risk | Último pedido >90 dias antes da última venda da base |
| revenue_target_missed | Receita <80% da meta sintética mensal |

Os alertas mostram valores medidos, não conclusões causais. Metas são fictícias.
Segmentação de rentabilidade usa P75 de receita de clientes e margem ponderada global,
com prioridade At Risk → Champions → High Revenue/Low Margin → High Margin → Low Value.
Segmentação é estática por snapshot; o campo cadastral `segment` é independente.
