# ADR-006: Publicação recuperável após commit do warehouse

**Status:** Implementada localmente; integração PostgreSQL pendente
**Data:** 08/10/2026
**Decisores:** manutenção técnica do projeto no escopo da revisão solicitada

## Contexto

O commit PostgreSQL encerrava o advisory lock. Um segundo pipeline poderia
commitar e publicar enquanto a primeira execução ainda exportava o snapshot
anterior. CSVs eram sobrescritos diretamente; falha de export exigia repetir a
ingestão. O exporter separado reconciliava com fontes locais potencialmente
alteradas e executava consultas com snapshots diferentes em READ COMMITTED.

## Decisão

Manter monólito modular, full refresh transacional e formatos financeiros.
Centralizar publicação em um serviço recuperável. Estender exclusão mútua até
publicação por lock de sessão PostgreSQL, na mesma conexão física. Recuperação
reconcilia raw/fato persistidos sob REPEATABLE READ, READ ONLY e o mesmo lock.
Substituir arquivos individualmente por rename; registrar status/hashes em
publication.json. Distinguir erro pós-commit de rollback no contrato da CLI.

## Opções consideradas

| Opção | Complexidade | Concorrência | Recuperação | Escolha |
|---|---|---|---|---|
| Reexecutar ETL após erro, lock transacional | Baixa | Pode publicar fora de ordem após commit | Recarga e dependência das fontes atuais | Rejeitada |
| Lock de sessão e serviço de publicação | Moderada | Serializa escritores/publicadores cooperantes | Sem nova ingestão, a partir do warehouse | Implementada |
| Outbox, worker e diretórios imutáveis por execução | Maior | Separa publicação de carga e permite retries duráveis | Estado auditável e retenção | Evolução quando houver operação contínua |

## Trade-offs

O lock de sessão mantém uma conexão ocupada durante I/O de arquivos e requer
conexão direta/pool de sessão. O tempo de publicação passa a integrar a duração
da exclusão mútua. O contrato CSV atual é mantido, por isso não existe atomicidade
de todo o bundle. O preflight de hashes não protege um refresh CSV concorrente.
O helper web continua responsável pelo manifest web existente.

## Consequências

Código 2 do pipeline significa warehouse commitado e publicação incompleta.
`python -m src.analytics.publication` recupera exports sem consultar CSVs locais.
`--verify` oferece preflight sem banco. O inicializador também coopera com o lock.
Scripts que modificam o warehouse sem essa chave continuam fora da proteção.
Uma publicação interrompida exige intervenção/retry; não há worker automático.

## Ações

1. [x] Capturar hash dos mesmos bytes usados pelo parser.
2. [x] Implementar lease e escrita atômica por arquivo.
3. [x] Implementar recuperação/reconciliação e verificador CSV.
4. [x] Cobrir falhas de arquivos e integridade com testes unitários.
5. [x] Executar integração PostgreSQL adicionada e checks Ruff em ambiente autorizado (15/10/2026).
6. [ ] Evoluir diretórios imutáveis e histórico de run antes de refresh concorrente.

Evidência e limites em [revisão de arquitetura](../architecture-review-2026-10-08.md).
