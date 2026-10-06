# Medidas DAX

Criar em `fact_sales` ou tabela dedicada de medidas. Sintaxe DAX com vírgulas;
ajustar separador à configuração regional do Desktop se necessário.
Formatar dinheiro em BRL, percentuais com 1–2 casas e contagens como inteiros.
As medidas funcionam sob os filtros das dimensões; margem por cliente/produto/canal
é a mesma `[Margem]` no contexto da dimensão, sem fórmulas duplicadas.

```dax
Receita Bruta = SUM(fact_sales[gross_revenue])
Descontos = SUM(fact_sales[discount_value])
Receita Líquida = SUM(fact_sales[net_revenue])
CMV = SUM(fact_sales[total_product_cost])
Frete = SUM(fact_sales[freight_allocated])
Devoluções = SUM(fact_sales[return_value])
Margem = SUM(fact_sales[contribution_margin])
Margem % = DIVIDE([Margem], [Receita Líquida])
Pedidos = DISTINCTCOUNT(fact_sales[order_id])
Ticket Médio = DIVIDE([Receita Líquida], [Pedidos])
Desconto Médio % = DIVIDE([Descontos], [Receita Bruta])
Quantidade Vendida = SUM(fact_sales[quantity])
Quantidade Devolvida = SUM(fact_sales[returned_quantity])
Quantidade Retida = [Quantidade Vendida] - [Quantidade Devolvida]
Taxa de Devolução = DIVIDE([Quantidade Devolvida], [Quantidade Vendida])
Clientes Ativos = DISTINCTCOUNT(fact_sales[customer_key])
Produtos Vendidos = DISTINCTCOUNT(fact_sales[product_key])
Receita Mês Anterior = CALCULATE([Receita Líquida], DATEADD(dim_date[full_date], -1, MONTH))
Margem Mês Anterior % = CALCULATE([Margem %], DATEADD(dim_date[full_date], -1, MONTH))
Variação Receita % = DIVIDE([Receita Líquida] - [Receita Mês Anterior], [Receita Mês Anterior])
Variação Margem pp = ([Margem %] - [Margem Mês Anterior %]) * 100
```

`DIVIDE` sem resultado alternativo retorna BLANK quando denominador é zero.
Mostrar “—” com tooltip “Não calculável: receita zero”, preservando a margem absoluta
negativa. Não representar receita zero como margem 0%, o que esconderia perdas de frete.
Contagens de clientes/produtos consideram pedidos não cancelados, inclusive devolvidos.
Desconto médio é ponderado pela receita bruta; devolução é taxa por unidades.

Criar tabela desconectada de What-if em Modeling → New Table:

```dax
Desconto Simulado = GENERATESERIES(0, 0.30, 0.01)
```

Formatar `Desconto Simulado[Value]` como percentual e criar slicer de seleção única.
As medidas abaixo substituem o desconto atual de cada item por um desconto uniforme.
Quantidade retida, custo unitário, mix, taxa de devolução e frete são mantidos.

```dax
Desconto Selecionado = SELECTEDVALUE('Desconto Simulado'[Value], 0)

Receita Simulada =
SUMX(
    fact_sales,
    ROUND(
        (fact_sales[quantity] - fact_sales[returned_quantity])
        * fact_sales[unit_price] * (1 - [Desconto Selecionado]),
        2
    )
)

Margem Simulada = [Receita Simulada] - [CMV] - [Frete]
Margem Simulada % = DIVIDE([Margem Simulada], [Receita Simulada])
Impacto na Margem = [Margem Simulada] - [Margem]

Volume Necessário % =
IF(
    [Margem Simulada] > 0 && [Margem] > 0,
    DIVIDE([Margem], [Margem Simulada]) - 1,
    BLANK()
)

Base sem Desconto =
SUMX(fact_sales, (fact_sales[quantity] - fact_sales[returned_quantity]) * fact_sales[unit_price])

Desconto Máximo para Margem 15% =
IF(
    [Base sem Desconto] > 0,
    1 - DIVIDE([CMV] + [Frete], [Base sem Desconto] * (1 - 0.15)),
    BLANK()
)
```

Volume necessário assume contribuição proporcional ao volume com custos variáveis
e mix constantes, incluindo frete proporcional. Não é previsão de demanda.
Resultado negativo indica que menor volume já preservaria a contribuição atual.
Se contribuição simulada <=0, nenhum crescimento positivo compensa a contribuição
atual positiva sob essas hipóteses. Limite de desconto negativo significa meta inviável
mesmo sem desconto; não truncar silenciosamente para zero.

Check manual obrigatório: exemplo preço=100, custo=63, frete=7, meta=15% →
17,6470588%; exemplo contribuição atual=50, simulada=30 → crescimento 66,6667%.
Pode haver diferença de centavos em relação à base histórica porque o simulador
arredonda diretamente a receita retida, enquanto o histórico arredonda desconto e
reembolso separadamente. Ambos seguem contratos documentados.
