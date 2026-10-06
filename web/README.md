# Showcase executivo

Next.js App Router, TypeScript, Tailwind e Recharts. Fonte: snapshots agregados
exportados por `python scripts/export_web.py` após nova reconciliação real.
Não conecta PostgreSQL, não recebe credenciais e não expõe clientes individualmente.

Na raiz do projeto, execute o pipeline; depois:

```powershell
cd web
npm ci
npm run lint
npm run typecheck
npm run build
npm run start
```

Abrir http://127.0.0.1:3000. Desenvolvimento: npm run dev.
Teste de navegador: `npx playwright install chromium` → `npx playwright test`.
O teste usa build de produção em desktop e mobile, verifica dados, filtro, navegação,
erros de página e overflow; screenshots locais em artifacts/web.

Metodologia em /methodology. O aviso de dados fictícios permanece no produto.
Metadata/OG estão configurados; robots=noindex enquanto a publicação for preview.
Domínio, canonical público e indexação devem ser ajustados no release com URL real.
O link ao repositório privado requer acesso. Deploy de produção executado em
06/10/2026: https://inteligence-bi-tau.vercel.app. O noindex permanece como decisão
de indexação da vitrine; publicação e indexação são independentes.
Evidências de CI e verificação remota: [registro de publicação](../docs/web-release.md).

`npm audit --omit=dev` passou sem vulnerabilidades runtime. Audit completo reportou
cinco high transitivos nas ferramentas ESLint/fast-glob/micromatch/braces, incluindo
braces<=3.0.3, sem versão corrigida disponível no registry consultado. Não foi aplicado
um downgrade forçado e incompatível de Next.js para ocultar o alerta. Revisar quando
houver patch; não apresentar o audit completo como limpo.
