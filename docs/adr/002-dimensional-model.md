# ADR 002: fato consolidada em item

Status: aceito para MVP. Decisão: agregar devoluções no item e ratear frete do pedido
antes de carregar analytics. Dimensões conformadas de data, produto, cliente, canal
e vendedor; keys derivadas dos IDs naturais estáveis, sem SCD2.

Isso evita duplicar receita em joins de frete/devoluções e simplifica DAX.
Alternativa futura: fato de eventos de devolução por data de retorno para análise
contábil temporal. Consequências: valores da venda histórica mudam no próximo
snapshot se houver novas devoluções; custos estáticos e atributos atuais substituem
o histórico. Não é uma camada contábil de competência nem warehouse incremental.
