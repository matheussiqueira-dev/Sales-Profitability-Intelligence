# ADR 004 — Showcase com snapshots agregados

Contexto: banco Docker local e vitrine Next.js que pode ser hospedada publicamente.
Decisão: exportar agregados após commit e reconciliação. Arquivos monetários têm
strings decimais; hashes validam integridade. Diretório de snapshot imutável por
hash e manifest trocado atomicamente após escrever todos os arquivos.

Next.js lê somente summary, meses, canais, produtos e segmentos de clientes.
Nenhum registro individual de cliente, senha ou conexão ao banco entra na aplicação.
Alternativa rejeitada: publicar PostgreSQL local ou incluir credencial no frontend.
Consequência: atualização do site requer export e novo build/deploy; não é realtime.
Build falha se arquivos ou hashes do snapshot não correspondem.
