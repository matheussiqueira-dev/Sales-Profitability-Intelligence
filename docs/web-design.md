# Direção do showcase

Público: gestor comercial/avaliador de Analytics Engineering. Pergunta visual:
quanto da receita sobrevive à sequência desconto → devolução → CMV → frete → taxas?
Elemento central: ponte financeira contínua, não uma coleção de cards decorativos.

Paleta: paper #FAFBFC; ink #17212B; muted #526271; line #DDE4EA;
revenue #2463A6; margin #08745B; loss #BC3941. Cor só para dados e seus significados.
Tipografia: Arial/Helvetica para leitura executiva, números tabulares; títulos com
escala moderada, sem depender de fonte externa. Conteúdo alinhado à esquerda.

Layout: cabeçalho compacto → mensagem de decisão + ponte financeira → faixa KPI →
série mensal e canais → quadrante/tabela produtos → arquitetura e metodologia.
Desktop tem grids minmax(0,1fr); mobile uma coluna, rótulos de gráficos legíveis,
tabela em região rolável identificada. Sem sombras/gradientes ou efeitos ornamentais.
Interações: escolher canal para comparação, escolher categoria no quadrante,
tooltip acompanhado de tabela acessível, links claros para metodologia e fonte.
Foco visível e redução de movimento; animações de charts desabilitadas.

Revisão do plano: removidos hero com número gigante e cards iguais porque esconderiam
a decomposição financeira. A ponte mostra os mesmos oito totais conciliados do DW.
Aviso de dados sintéticos e contrato V2 perto dos KPIs; nenhum screenshot de Power BI
é inventado. A aplicação lê somente snapshots agregados, com hashes conferidos.
