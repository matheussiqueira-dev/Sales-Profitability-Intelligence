# Validação real do Power BI V2 — 06/10/2026

Power BI Desktop Store 2.158.1177.0. PBIP aberto, modelo carregado e salvo no Desktop.
Cinco páginas PBIR: Executivo, Produtos, Clientes, Canais, Simulador.
O projeto foi inicialmente carregado pelos CSVs de snapshot exportados do PostgreSQL
conciliado. Parâmetros M permitem alternar SourceMode para PostgreSQL; autenticação
da conexão direta será validada separadamente e não é inferida da carga CSV.

Consultas DAX executadas no Analysis Services local do Desktop via ADOMD 19.84.1.
`scripts/compare_powerbi.py` compara esses resultados com a fato persistida e a
função Python de simulação; relatório completo local em artifacts/powerbi-parity.json.

| Métrica | SQL/Python | DAX | Diferença R$ |
|---|---:|---:|---:|
| Receita bruta | 126.264.177,15 | 126.264.177,15 | 0,00 |
| Desconto | 12.663.500,58 | 12.663.500,58 | 0,00 |
| Devolução | 3.605.814,43 | 3.605.814,43 | 0,00 |
| Receita líquida | 109.994.862,14 | 109.994.862,14 | 0,00 |
| CMV | 72.970.809,50 | 72.970.809,50 | 0,00 |
| Frete | 2.178.770,47 | 2.178.770,47 | 0,00 |
| Custos variáveis | 9.740.706,54 | 9.740.706,54 | 0,00 |
| Contribuição | 25.104.575,63 | 25.104.575,63 | 0,00 |

| Desconto uniforme | Receita simulada | Custos variáveis | Contribuição | Paridade monetária |
|---|---:|---:|---:|---|
| 0% | 122.274.178,39 | 10.956.162,94 | 36.168.435,48 | diferença zero |
| 10% | 110.046.818,61 | 9.889.311,76 | 25.007.926,88 | diferença zero |
| 20% | 97.819.342,71 | 8.822.459,13 | 13.847.303,61 | diferença zero |
| 30% | 85.591.984,58 | 7.755.607,32 | 2.686.797,29 | diferença zero |

Falha identificada por execução real: GENERATESERIES com Double omitia 30% e
taxas em Double criavam diferenças de centavos. Corrigido com parâmetro Currency
e cálculos por centavos/basis points + QUOTIENT, retornando CURRENCY em cada linha
antes de SUMX. A implementação pressupõe valores escalados dentro do intervalo
exato de inteiros do motor numérico; o dataset sintético validado satisfaz esse limite.
Isso reproduz HALF_UP para valores não negativos do contrato.

Margem global 22,8234075%; teto analítico para meta 15% = 19,1147813%.
Teto agregado pondera taxa pela base sem desconto. Percentuais têm precisão do
motor DAX; a exigência de tolerância zero se aplica aos totais monetários em centavos.

JSONs PBIR validados nos schemas oficiais Microsoft; TMDL validado pelo serializer
Microsoft. Esses checks são complementares à execução real registrada acima.
Gate de publicação externa (Power BI Service/Publish to web) não executado.
