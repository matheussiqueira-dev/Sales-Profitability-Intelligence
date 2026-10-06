# ADR 003 — Migração financeira e DDL explícito

Contexto: warehouse V1 populado, sem custos variáveis, criado com metadados SQLAlchemy.
Decisão: DDL físico raw/staging versionado em SQL; contratos Python geram esse arquivo
por script separado, e CI verifica drift. Loader executa SQL, não infere tabelas.
Migração 002 adiciona colunas com zero para snapshot legado, mantém registros,
remove somente o CHECK antigo de contribuição e instala invariantes V2.
Marker de posse é verificado antes de qualquer migração; schema_migrations registra versão.

A migração e a carga/reconciliação compartilham transação quando executadas pelo
pipeline. Backup V1 preservado antes de aplicar localmente. Upgrade com registros e
totais preservados e rollback foram testados no banco isolado.
Zero legado significa custo não modelado na versão anterior; só a carga de
variable_costs produz contribuição V2 completa. Não se apresenta zero legado como
prova de ausência de taxas. Alternativa rejeitada: apagar banco/recriar volumes.

DDL V2 novo tem checks de ranges; tabelas antigas mantêm os contratos físicos
originais para campos inalterados, com validação Pandera/relacional antes da carga.
Migrações futuras devem revisar checks/índices adicionais explicitamente.
