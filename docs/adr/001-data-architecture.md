# ADR 001: snapshot PostgreSQL e Python

Status: aceito para MVP local. Contexto: reproduzir um case completo sem depender
de Power BI para limpar dados ou validar dinheiro. Decisão: CSV sintético → Python
com contratos → PostgreSQL em três schemas → Power BI Import.
Python/Decimal permite testes unitários das regras e centavos exatos; Pandas cuida
de joins e agrupamentos. psycopg 3 tem binários para o Python instalado; evita
compilação de drivers. Full refresh transacional favorece reprodutibilidade e rollback.

Alternativas: CSV direto no Power BI não exercita DW/qualidade; dbt/orquestrador
seriam complexidade adicional para 100 mil itens locais. Consequências: dados e
memória precisam caber no processo, sem histórico de execuções raw nem incremental.
