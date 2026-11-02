# Entrega V2 — 06/10/2026

## Estado verificado

Planning adaptado sobre main 33a5624, sem reconstruir projeto. Preservados licença,
alterações locais preexistentes e todos os registros do dataset V1.
Repositório verificado como PRIVATE; não foi alterada a visibilidade.

| Gate | Evidência |
|---|---|
| Baseline preservada | 59 testes e backup artifacts/baseline-v1/postgres.dump |
| Contrato financeiro V2 | Fonte variável, três colunas na fato, Python/SQL/DAX com custos |
| Fonte determinística | RNG separado para embalagem; sete CSVs V1 preservados |
| Pandera | lazy checks declarativos, Decimal exato, regras relacionais mantidas |
| DDL e migração | DDL versionado, migração 002, fresh DB, upgrade, rollback, lock |
| Base completa | 99.235 itens não cancelados e oito totais conciliados, diferença zero |
| Testes completos | 69 passed, 92% cobertura; unidade e integração diferenciadas |
| Power BI estrutural | Microsoft TOM/TMDL parser e checks PBIR passaram |
| Power BI executado | PBIP aberto/carregado/salvo; DAX via motor local, oito métricas iguais |
| Cenários | 0/10/20/30% conferidos em Python e DAX, diferença monetária zero |
| Web | lint, typecheck, build; duas rotas estáticas e dois testes Playwright verdes |
| Integridade pública | cinco JSONs agregados por hash; nenhum segredo ou cliente individual |
| UI web | screenshots reais desktop/mobile; navegação/filtro/sem overflow conferidos |
| Audit runtime web | npm audit --omit=dev: zero; full audit com cinco high só em tooling |
| CI V2 | cinco jobs remotos aprovados; ver registro de publicação web |

Base: 2.000 clientes, 200 produtos, 40.000 pedidos, 101.772 itens, 4.366 devoluções,
40.000 fretes, 96 metas e 101.772 contratos de custo. Fato: 99.235 itens / 39.002 pedidos.
Receita líquida R$109.994.862,14; custos variáveis R$9.740.706,54; contribuição
R$25.104.575,63; margem 22,8234075%; dez regras produziram 165 alertas.
Os totais financeiros V1 foram mantidos nos relatórios históricos, sem comparação
enganosa com a métrica V2 que agora inclui outra categoria de custo.

Documentação: contratos/modelo/dicionário atualizados, ADRs 003–005, três achados,
plano de execução adaptado, guia web, projeto PBIP/TMDL/PBIR e validation.md.

## Limites e gates pendentes

- Conexão PostgreSQL direta no Desktop está na tela de autenticação manual.
  O modo snapshot CSV já foi validado, mas isso não prova a conexão direta.
- Revisão visual final de cinco páginas, screenshots Power BI, filtros sincronizados,
  acessibilidade/mobile Power BI e demonstração GUI do What-if ainda pendentes.
  Os cenários foram efetivamente executados pelo motor DAX, sem alegar GUI testada.
- Desktop adicionou tabelas ocultas de datas automáticas; desativação/mark date table
  permanece melhoria semântica. As cinco relações de negócio foram verificadas.
- Algumas revisões de schema PBIR emitidas pelo Desktop não estavam publicadas
  no endpoint oficial. Compatibilidade com schema anterior foi registrada;
  isso não é apresentado como validação exata da revisão indisponível.
- Full npm audit detecta vulnerabilidade transitiva sem patch publicado em braces
  de ferramentas dev. Runtime está limpo. Não aplicado downgrade incompatível.
- Push V2, CI remota V2 e deploy web foram concluídos posteriormente conforme
  [registro de publicação](../web-release.md). Publicação no Power BI Service e
  abertura de visibilidade do repositório não executadas.

Não se considera release pública concluída com esses gates abertos. Nenhum PBIX,
imagem de Power BI ou resultado de teste foi fabricado. Para retomar: concluir
autenticação no Desktop → reconferir DAX/refesh → revisar visuais → publicar após revisão.
