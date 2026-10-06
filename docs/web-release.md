# Publicação da V2 — 06/10/2026

Publicação no GitHub e na Vercel autorizada pelo usuário. Projeto existente:
`inteligence-bi`, ID `prj_AxjFctZoHX7n6GbtMLOzFRl7VpgA`.
O deploy anterior do commit `33a5624` falhou com `PYTHON_ENTRYPOINT_NOT_FOUND`.
A configuração foi corrigida para Next.js, raiz `web`, Node.js 22.

## Validação local antes da publicação

- 69 testes Python aprovados, incluindo PostgreSQL isolado; cobertura de 92%.
- Ruff, formatação e consistência do DDL aprovados.
- 39 arquivos JSON Power BI e parser Microsoft TMDL aprovados, com as exceções
  de compatibilidade de schema já descritas em `powerbi/validation.md`.
- Instalação reproduzível, lint, TypeScript e build Next.js aprovados.
- Dois testes Playwright aprovados: desktop e celular, filtros e navegação.
- Auditoria das dependências de produção: zero vulnerabilidades.
- Auditoria de arquivos para credenciais locais aprovada.

O parâmetro SourceMode salvo pelo Desktop agora é PostgreSQL. A autenticação
direta e a revisão visual final do Power BI continuam pendentes; este deploy
publica a aplicação web com o snapshot agregado conciliado, sem expor o banco.
Cinco alertas altos em dependências transitivas das ferramentas de desenvolvimento
continuam documentados. A publicação não encerra esses itens do Power BI.

## Evidências remotas

- Commit de implementação `843a5070521fe3f725beedf68577f137ddec376c`, confirmado
  em `origin/main` após o push.
- [CI 37532672986](https://github.com/matheussiqueira-dev/Sales-Profitability-Intelligence/actions/runs/37532672986):
  os cinco jobs passaram — Python 3.12, Python 3.13, PostgreSQL, web e artefatos BI.
- Vercel: deploy `dpl_6A2xozQsqUmXAhw2mAqyVg6X8bhc`, produção, mesmo SHA,
  estado READY, sem erro de associação de domínio. Build remoto em aproximadamente
  34 segundos, após a espera na fila.
- [Domínio público](https://inteligence-bi-tau.vercel.app): HTTP 200 e título
  correto, sem login. O alias longo da equipe exige autenticação; a proteção foi preservada.
- Navegador remoto: desktop 1440×1000 e celular 390×844; valor 22,8%, conciliação,
  filtro de categoria, tabela e metodologia conferidos. Sem overflow, erro JavaScript
  ou resposta HTTP de erro nos recursos da aplicação.
- Consulta de erros de runtime na última hora: nenhum erro encontrado.
  Consulta dos logs de erro/fatal nos últimos 30 minutos: nenhum registro encontrado.
  Não há drains configurados. Isso comprova a janela consultada, sem prometer
  monitoramento contínuo, alertas futuros ou medições de usuários reais.

O commit de documentação subsequente registra essas evidências e será novamente
verificado na CI e na publicação automática da integração Git da Vercel.
