# Três achados do case V2

Base sintética seed 42, 2024–2025. Cálculos conciliados no PostgreSQL e no motor DAX.
São observações do cenário construído, não resultados de empresa ou benchmarks.

1. **Custos variáveis mudam materialmente a leitura de rentabilidade.**
   Taxas e embalagem somam R$9.740.706,54. A contribuição passa de
   R$34.845.282,17 (V1, sem essa categoria) para R$25.104.575,63 (V2).
   Receita líquida permanece R$109.994.862,14; margem V2 é 22,82%.
   Decisão: avaliar campanhas/negociações pela métrica completa, não pelo número V1.

2. **Marketplace lidera receita, mas apresenta a menor margem percentual.**
   O showcase usa os valores da view conciliada; a taxa de canal sintética de 14,5%
   é parte relevante desse comportamento, junto ao mix, desconto e frete.
   Venda Direta tem a maior margem percentual. Decisão: comparar contribuição
   incremental por canal e revisar condições; os dados não estabelecem causalidade.

3. **Desconto uniforme de 20% derruba a contribuição abaixo da meta de 15%.**
   Receita simulada R$97.819.342,71; contribuição R$13.847.303,61;
   margem 14,16%. O teto analítico agregado para margem de 15% é 19,11%.
   Decisão: usar teto por contexto/produto e verificar cenários em centavos,
   em vez de aplicar desconto máximo único a todo cliente.

Limites: estoque/capacidade/elasticidade não modelados; volume compensatório não é
previsão. Impostos/CAC/custos fixos/perdas em devolução ausentes. Embalagem mantida
mesmo na devolução. Contribuição é atribuída ao período da venda, não evento contábil.
