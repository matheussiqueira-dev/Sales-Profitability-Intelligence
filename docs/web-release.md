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

Resultados remotos serão registrados após concluir a CI e verificar o deploy.
