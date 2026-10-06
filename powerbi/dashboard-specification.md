# Cinco páginas de decisão comercial

Evolução V2: cinco páginas PBIR foram criadas, abertas, carregadas e salvas no Desktop;
totais e cenários DAX executados e conciliados (validation.md). As recomendações
visuais e interações abaixo continuam como critérios de revisão, não se assume que
todo refinamento foi implementado por existir uma especificação. Screenshots finais,
filtros sincronizados, acessibilidade e autenticação PostgreSQL devem constar do
relatório V2 com evidência específica. A especificação V1 permanece como referência.

Status: especificação pronta; implementação visual e testes no Desktop pendentes.
Público: gestores comerciais e analistas. Pergunta central: o crescimento de receita
está produzindo contribuição suficiente depois de descontos, devoluções e logística?

Canvas 16:9 (1280×720), fundo #F7F8FA, texto #18212B, bordas #D8DEE6;
tipografia Segoe UI, títulos 22–26 pt, KPIs 26–32 pt, rótulos >=11 pt.
Grid com margem externa 24 px, espaços entre visuais 16 px e títulos alinhados.
Cor reservada aos dados: azul #175CD3 para receita, verde #087443 para contribuição,
vermelho #B42318 para perdas, âmbar #8A4B08 para atenção. Sempre combinar cor com
rótulo/ícone/texto; evitar arco-íris e depender exclusivamente de vermelho/verde.
Tooltips explicitam denominador, regra financeira e período; unidades iguais em
visuais comparáveis. Navegação consistente no topo, seleção ativa também sublinhada.

## 1. Visão executiva

Título: “Vendas e rentabilidade”; subtítulo período selecionado e origem sintética.
Filtros sincronizados: período, canal, região do cliente e categoria; botão limpar.
Primeira linha: receita líquida, contribuição, margem %, pedidos, ticket médio;
segunda faixa compacta: desconto ponderado, devolução por unidades, clientes ativos.
Série temporal receita × contribuição com eixo monetário compartilhado; margem % em
visual separado para evitar eixo duplo confuso. Barras horizontais de contribuição
por canal; receita por categoria; top 10 e bottom 10 produtos por contribuição absoluta.
Painel de sinais com valor, limiar e próxima investigação (sem afirmar causalidade).

## 2. Produtos

Scatter: X receita líquida, Y margem %, tamanho quantidade vendida, cor categoria.
Linhas de referência: receita P75 e margem ponderada do portfólio, recalculadas no
contexto de filtros mantendo todos os produtos selecionados. Mostrar quadrantes
“Alta receita / Alta margem”, “Alta receita / Baixa margem”, “Baixa receita / Alta
margem” e “Baixa receita / Baixa margem”. Pontos sem receita zero ficam em tabela
separada; tooltip explica por que margem % não existe.
Matriz: produto, receita, quantidade, CMV, desconto, frete, devolução, contribuição,
margem %, desconto máximo para meta de 15%. Valores negativos com sinal e legenda.
Drill-through para produto; selecionar ponto filtra tabela, com affordance visível.

## 3. Clientes

KPIs receita, contribuição, margem %, ticket, desconto ponderado, pedidos e devoluções.
Scatter X receita, Y margem %, tamanho número de pedidos. Lista pesquisável e
drill-through com histórico mensal. Segmentação estática entregue pela view:
At Risk primeiro (>90 dias sem pedido em relação à última venda da base);
depois receita >=P75 + margem >=margem ponderada = Champions;
receita >=P75 + margem menor = High Revenue / Low Margin;
demais acima da margem média = High Margin; restantes = Low Value.
Separar esse segmento do campo `segment` cadastral (Enterprise/Corporate/SMB/Consumer).
Label explícito “segmentação do snapshot completo” quando usada sob filtros.

## 4. Canais

Comparar Loja Física, E-commerce, Marketplace e Venda Direta. Barras de receita e
contribuição com escalas monetárias iguais, ranking de margem %, tabela de desconto,
frete, ticket e taxa de devolução. Tooltip “custos incluem CMV e frete; comissões e
impostos não modelados”. Perguntas respondidas: quem vende mais, quem contribui mais,
quem apresenta maior peso de frete? Metas mensais sintéticas em visual separado.

## 5. Simulador

Slicer uniforme 0–30%, passo 1%, seleção única; exibir desconto atual ponderado e
simulado lado a lado. KPIs receita simulada, contribuição simulada, margem simulada,
impacto e crescimento de volume necessário. Exibir premissas no canvas: mix,
quantidade retida e custos constantes; compensação de volume proporcional.
Estado de inviabilidade se contribuição <=0; não exibir infinito ou 0% enganoso.
Tabela por produto com teto de desconto para margem mínima de 15% e indicação textual
quando nem preço de lista atinge a meta.

## Checklist visual e de interação no Desktop

- Sem filtros: KPIs coincidem com view summary e relatórios de reconciliação.
- Filtros sincronizam páginas 1–4; seleção do simulador permanece desconectada.
- Nenhum resultado: mensagem “Nenhuma venda no período/filtro selecionado” e limpar filtros.
- Receita zero: margem % “—”; contribuição absoluta permanece visível.
- Order de tabulação lógica, alt text informativo em cada visual e navegação por teclado.
- Cor acompanhada de rótulo; contraste avaliado no canvas real, inclusive tooltip.
- Fontes e rótulos legíveis em apresentação; sem títulos truncados ou tabela ilegível.
- Conferir Desktop maximizado e layout mobile separado do Power BI; adaptar para
  uma coluna, KPIs antes de gráficos, filtros acessíveis, sem reusar canvas reduzido.
- Registrar screenshots reais somente depois de construir e executar essas verificações.

Os cuidados visuais foram revisados a partir da skill senior-ui-polish. Como não há
interface web ou PBIX construído, não houve QA de navegador/mobile nem validação
visual em Power BI. Esta especificação não é evidência de acessibilidade implementada.
