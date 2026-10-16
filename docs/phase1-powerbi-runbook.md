# Fase 1 — finalizar e comprovar o Power BI

## 1. Objetivo e limite desta execução

Entregar o PBIP existente com conexão PostgreSQL verificada, dados atualizados,
cinco páginas revisadas, interações testadas e evidências reais. A implementação
financeira já existe: não recriar o projeto, gerar novamente o PBIR ou substituir
medidas DAX para reproduzir a especificação antiga.

Este roteiro descreve trabalho a executar. Não é declaração de que a fase passou.
Não publica no Power BI Service, não muda a visibilidade do GitHub e não faz deploy
web. Essas entregas ou decisões são separadas. Não altera o escopo das fases 2–5.

**Arquivo principal:** `powerbi/project/SalesProfitability.pbip`.
**Automação:** `scripts/phase1_powerbi.ps1`.
**Motor financeiro:** Python Decimal + PostgreSQL numeric + medidas DAX Currency.
**Dados:** sintéticos. Margem de contribuição não representa lucro líquido.

## 2. Comandos exatos

Execute em **PowerShell 7 (`pwsh`)**, sem necessidade de executar como administrador.
As bibliotecas Microsoft usadas pelos verificadores são .NET; o Windows PowerShell
5.1 (`powershell.exe`) não é o ambiente previsto para este script.

```powershell
Set-Location -LiteralPath 'C:\Users\mathe\Documents\Programação\Sales Profitability Intelligence'
pwsh -NoProfile -File .\scripts\phase1_powerbi.ps1 -Mode Prepare
```

Se o banco deste projeto estiver parado, use explicitamente:

```powershell
pwsh -NoProfile -File .\scripts\phase1_powerbi.ps1 -Mode Prepare -StartPostgres
```

O segundo comando inicia somente o serviço `postgres` do Compose deste repositório.
Pode recriar o container para aplicar a configuração existente, preservando o volume.
Não remove volumes, não reinicializa o warehouse e não executa a carga ETL.

Pré-requisitos: `.venv`, dependências instaladas pelo setup do projeto, `.env`
configurado localmente, Git, acesso à internet para schemas/NuGet e base já carregada.
Não copiar a senha para o script. Se existirem variáveis POSTGRES_* no terminal,
elas prevalecem sobre `.env`; confira os nomes sem imprimir valores sensíveis.
Use a base `sales_profitability`, nunca uma base terminada em `_test` nesta fase.

O script termina com código 0 se o modo solicitado passou, ou 1 se uma etapa falhou.
Mesmo código 0 **não declara a fase concluída**: a revisão manual continua obrigatória.

## 3. O que Prepare faz, em ordem

1. Localiza a raiz pelo caminho do próprio script e restaura a pasta original ao terminar.
2. Cria uma pasta exclusiva em `artifacts/phase1/<data-UTC>-<id>`.
3. Confere Python local, `.env`, PBIP e consistência das dependências (`pip check`).
4. Registra commit, alterações locais e versão PowerShell em `environment.json`.
5. Copia os arquivos versionados de `powerbi/` para `backup/powerbi/` dentro da sessão.
   A cópia preserva o conteúdo em disco, inclusive mudanças ainda não commitadas nesses
   arquivos. Não captura mudanças ainda não salvas no Desktop nem arquivos novos
   não versionados; salve antes e preserve esses arquivos separadamente se existirem.
6. Inicia PostgreSQL somente se `-StartPostgres` foi fornecido.
7. Executa o verificador de warehouse, que lê tabelas, resumo e metadados e grava
   `data/processed/database-verification.json`; copia o resultado para `warehouse.json`.
8. Verifica candidatos ao Git procurando credenciais locais e tokens conhecidos.
   É uma checagem complementar, não prova absoluta de ausência de segredos.
9. Valida os arquivos PBIR. As revisões de schema sem publicação oficial continuam
   identificadas como verificações de compatibilidade, não validações exatas.
10. Baixa TOM/ADOMD 19.84.1 oficiais, verifica SHA512 e executa o parser TMDL.
11. Grava etapas, duração e estado em `result.json`.

Downloads ficam em `artifacts/tom` e `artifacts/adomd`; não há instalação global.
A automação não abre telas de login, não lê a senha para imprimi-la, não altera
o modelo aberto, não remove tabelas e não aprova qualidade visual.
Execute depois de salvar e em uma sessão dedicada, sem outra carga ou edição
simultânea do modelo. A configuração padrão de saída deve ser `data/processed`.

## 4. Abrir o projeto certo

1. Salve alterações de outros relatórios e feche-os para facilitar a identificação
   do motor Analysis Services ativo.
2. No Desktop, abra **SalesProfitability.pbip** da pasta deste repositório.
3. Confira as páginas **Executivo, Produtos, Clientes, Canais e Simulador**.
4. Confira a presença de `fact_sales`, `dim_date`, `dim_customer`, `dim_product`,
   `dim_channel`, `dim_seller` e `Desconto Simulado`.
5. Anote a versão efetivamente usada do Power BI Desktop e a data da revisão.
6. Não use `generate_powerbi.py` para corrigir uma tela: o gerador pode substituir
   refinamentos já salvos no projeto. Edite o relatório existente no Desktop.

## 5. Conexão direta e atualização — etapa manual

No gerenciamento de parâmetros do Power Query, confira:

| Parâmetro | Valor esperado neste computador |
|---|---|
| SourceMode | PostgreSQL |
| ServerName | 127.0.0.1:5432 |
| DatabaseName | sales_profitability |
| DataFolder | C:/Users/mathe/Documents/Programação/Sales Profitability Intelligence/data/processed |

`DataFolder` serve ao modo Snapshot. Em outro computador, adapte ao clone real.
Host, porta e banco precisam corresponder à configuração local; os valores acima
não substituem os parâmetros de um ambiente diferente.

1. Aplique os parâmetros e inicie a atualização.
2. Na solicitação de credenciais PostgreSQL, escolha a autenticação compatível
   com o usuário/senha do banco. Digite pessoalmente os valores da configuração local.
3. Armazene a credencial somente no mecanismo de credenciais do Desktop.
4. Se houver erro de credencial, verifique a origem selecionada em configurações
   de fonte de dados; não troque para Snapshot apenas para declarar a conexão aprovada.
5. Aguarde o carregamento de todas as tabelas e confirme que nenhuma consulta falhou.
6. Salve o PBIP.
7. Registre uma captura da atualização concluída e outra dos parâmetros, com campos
   de senha e outros valores sensíveis fora da imagem.

**Aceite:** SourceMode PostgreSQL, refresh concluído sem erro e valores conferidos
na próxima etapa. Um arquivo TMDL dizendo PostgreSQL não comprova conexão real.
A igualdade dos totais também não identifica sozinha a origem dos dados.

## 6. Executar a validação financeira nova

Depois do refresh, mantenha somente este relatório aberto e execute:

```powershell
pwsh -NoProfile -File .\scripts\phase1_powerbi.ps1 -Mode Validate
```

O script procura arquivos `msmdsrv.port.txt` nas instalações Store e convencional,
lê a porta e confirma que há um serviço TCP ativo. Só seleciona automaticamente
quando encontra exatamente uma porta ativa. Isso não substitui conferir qual
relatório está aberto; fechar os outros evita comparar o modelo errado.

Se a descoberta for ambígua, consulte as portas:

```powershell
$taskWorkspacePaths = @(
  (Join-Path $env:USERPROFILE 'Microsoft\Power BI Desktop Store App\AnalysisServicesWorkspaces'),
  (Join-Path $env:LOCALAPPDATA 'Microsoft\Power BI Desktop\AnalysisServicesWorkspaces')
)
foreach ($taskWorkspacePath in $taskWorkspacePaths) {
  if (Test-Path -LiteralPath $taskWorkspacePath) {
    Get-ChildItem -LiteralPath $taskWorkspacePath -Filter msmdsrv.port.txt -Recurse -File |
      ForEach-Object {
        [pscustomobject]@{Arquivo=$_.FullName;Porta=[IO.File]::ReadAllText($_.FullName).Trim()}
      }
  }
}
```

Feche outros relatórios e repita a descoberta. Se necessário, informe a porta
confirmada, substituindo o número deste **exemplo**:

```powershell
pwsh -NoProfile -File .\scripts\phase1_powerbi.ps1 -Mode Validate -Port 59212
```

A porta do motor Desktop muda ao reabrir o relatório. **Não use 5432**: essa é a
porta PostgreSQL. Consultas DAX são enviadas ao Analysis Services local.

Validate repete os checks Prepare, consulta `validation.dax` e `scenarios.dax`,
grava resultados novos na sessão e executa `compare_powerbi.py`. Os aliases de
resultados em `artifacts/powerbi-*.json` são atualizados; cada sessão preserva seus
próprios resultados. Não aceite um JSON antigo como evidência da atualização atual.

### Valores de referência do dataset atual

Sem filtros, os oito totais monetários devem apresentar diferença **R$0,00**:

| Métrica | Valor de referência |
|---|---:|
| Receita bruta | R$126.264.177,15 |
| Descontos | R$12.663.500,58 |
| Devoluções | R$3.605.814,43 |
| Receita líquida | R$109.994.862,14 |
| CMV | R$72.970.809,50 |
| Frete | R$2.178.770,47 |
| Custos variáveis | R$9.740.706,54 |
| Margem de contribuição | R$25.104.575,63 |

São referências do snapshot validado, não constantes a gravar em medidas.
Se a base mudou intencionalmente, gere evidência nova e documente a alteração.
`parity.json` é o aceite financeiro contra o banco realmente consultado.
Margem percentual aproximada: 22,8234075%; pedidos não cancelados: 39.002.

| Desconto uniforme | Receita simulada | Custos variáveis simulados | Contribuição simulada |
|---|---:|---:|---:|
| 0% | R$122.274.178,39 | R$10.956.162,94 | R$36.168.435,48 |
| 10% | R$110.046.818,61 | R$9.889.311,76 | R$25.007.926,88 |
| 20% | R$97.819.342,71 | R$8.822.459,13 | R$13.847.303,61 |
| 30% | R$85.591.984,58 | R$7.755.607,32 | R$2.686.797,29 |

O cenário 10% não tem obrigação de coincidir com o histórico: ele aplica desconto
uniforme a todas as linhas, enquanto os descontos históricos variam.

## 7. Calendário e relações

1. Revise o uso das hierarquias automáticas nos visuais antes de desativá-las.
2. Na configuração de carregamento de dados do **arquivo atual**, desative
   Auto date/time. Não altere preferências globais de outros projetos.
3. Use `dim_date[full_date]` como a coluna de calendário. Neste modelo, siga a
   estratégia de tabela de datas explícita; marque a tabela pelo recurso do Desktop
   apropriado à versão instalada, validando datas únicas, sem nulos e contínuas.
4. Refaça eixos que dependiam de hierarquias automáticas usando atributos `year`,
   `month`, `month_name` e a coluna de data da dimensão.
5. Ordene nome de mês pelo número do mês; confira a ordem temporal dos gráficos.
6. Confira cinco relações de negócio: dimensão no lado 1, `fact_sales` no lado N,
   chaves date/customer/product/channel/seller e direção de filtro coerente.
7. `Desconto Simulado` deve permanecer desconectada da fato.
8. Salve, feche, reabra e execute Validate novamente. Inspecione o diff TMDL/PBIR;
   remoção de tabelas automáticas não pode apagar medidas ou dimensões de negócio.

Referências: [tabelas de datas](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-date-tables)
e [Auto date/time](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-auto-date-time).

## 8. Revisão das cinco páginas

Use `powerbi/dashboard-specification.md` como referência visual, observando que há
textos V1 históricos. Para V2, custos incluem pagamento, canal, comissão e embalagem.
Corrija qualquer tooltip que diga que comissões não estão modeladas. Impostos,
despesas fixas e lucro líquido não foram modelados.

| Página | Conferências mínimas e evidência |
|---|---|
| Executivo | Cinco KPIs legíveis, período e origem sintética visíveis, receita versus contribuição, rankings coerentes; captura sem filtros e outra filtrada |
| Produtos | Scatter com receita no X, margem no Y, quantidade no tamanho; referências explicadas, perdas com sinal; selecionar ponto deve ter efeito coerente na tabela |
| Clientes | Segmentos de rentabilidade diferenciados do segmento cadastral; rótulo indica segmentação do snapshot completo; conferir seleção e contexto dos totais |
| Canais | Quatro canais, escalas comparáveis, receita e contribuição diferenciadas; tooltip financeiro V2 e ordenação sem ambiguidade |
| Simulador | Seleção única 0–30%, todos os percentuais disponíveis, premissas visíveis, métricas e estados de inviabilidade consistentes |

Em todas: alinhamento, tamanho de fonte, unidades, títulos sem corte, tabelas
legíveis, sinal negativo preservado, legenda e nomes compreensíveis. Mantenha o
canvas 16:9, Segoe UI e cor reservada aos dados. Evite converter percentuais em
somas: margem agregada deve ser contribuição dividida pela receita líquida.

Recursos da especificação ainda ausentes devem ser implementados e testados, ou
registrados explicitamente como diferença de escopo; não marcar como concluídos
somente porque o texto os descreve.

## 9. Matriz manual de filtros e estados

Crie `artifacts/phase1/<sessao>/manual-review.csv` com colunas:
`id,pagina,acao,esperado,observado,status,evidencia,revisor,data`.
Status permitidos: `APROVADO`, `REPROVADO`, `PENDENTE`, `NAO_APLICAVEL_COM_JUSTIFICATIVA`.

Execute e registre ao menos:

1. F01: sem filtros, conferir os oito totais contra a validação automatizada.
2. F02: selecionar um canal; conferir atualização das métricas e páginas 1–4.
3. F03: selecionar categoria e período; conferir interseção dos filtros.
4. F04: navegar entre páginas; conferir filtros sincronizados, mesmo se o controle
   não estiver visível em todas as páginas.
5. F05: limpar filtros; voltar exatamente à referência sem filtros.
6. F06: selecionar um produto/cliente; conferir os efeitos de destaque ou filtro
   configurados e testar drill-through quando disponível.
7. F07: filtrar para período sem vendas; apresentar ausência de dados claramente,
   sem divisão inválida, infinito ou métricas históricas residuais.
8. F08: verificar a regra de receita zero/margem indefinida. Se a base não contém
   esse caso, registre a limitação e use uma fixture isolada para validá-lo;
   não insira linhas artificiais no warehouse principal.
9. F09: no simulador, escolher 0%, 10%, 20%, 30%, sem filtros adicionais; conferir
   valores da tabela da seção 6, ou evidência nova se o dataset mudou.
10. F10: escolher 1%, 18% e 29%; conferir que o controle aceita passos intermediários.
11. F11: trocar apenas o desconto e conferir que as páginas históricas não mudam.
12. F12: se contribuição simulada for <=0 em um cenário admissível, mostrar
   inviabilidade e crescimento necessário indefinido de forma explícita. Se o
   dataset/intervalo atual não produz esse caso, registrar como não exercitado;
   não alterar o intervalo só para fabricar uma captura.

Use o painel de sincronização de segmentações para decidir quais páginas
sincronizam e quais mostram cada controle. O desconto What-if deve ser separado.

## 10. Acessibilidade e layout mobile

1. Em cada visual, configure texto alternativo útil: pergunta respondida, unidade
   e interação. Não repetir apenas “gráfico”.
2. Organize a ordem de tabulação: navegação → filtros → KPIs → gráficos → tabelas.
   Remova elementos puramente decorativos dessa ordem.
3. Percorra todas as páginas usando teclado; confira foco visível, seleção e limpeza.
4. Não use somente cor para comunicar perdas: mantenha sinal, texto ou legenda.
5. Confira contraste de textos/rótulos, inclusive tooltips, no canvas real.
6. No modo de layout mobile, monte cada uma das cinco páginas em uma coluna:
   KPIs primeiro, filtros acessíveis, gráficos depois e tabelas adequadas ao espaço.
7. Teste interações na visualização mobile. Isso não comprova uso em um dispositivo
   físico; caso não teste no aplicativo móvel, registre essa limitação.

Referências oficiais: [acessibilidade](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports)
e [layout mobile](https://learn.microsoft.com/power-bi/create-reports/power-bi-create-mobile-optimized-report-mobile-layout-view).

## 11. Best Practice Analyzer (BPA)

O script valida TMDL, mas **não executa BPA** e não instala Tabular Editor.

1. Use a versão disponível do Tabular Editor que suporte o modelo/forma de conexão
   selecionada. Registre versão, forma de acesso e versão/hash das regras aplicadas.
2. Consulte a documentação da versão antes de usar comandos; TE2 e a CLI atual
   têm sintaxes diferentes. Não copiar um comando de outra versão.
3. Abra o modelo existente ou conecte ao Desktop correto e execute a análise.
4. Revise descrições, formatos, pastas de exibição, sumarização de chaves, relações,
   colunas ocultas e propriedades do calendário.
5. Corrija manualmente os achados pertinentes. Não aplique todas as sugestões
   de forma automática, especialmente mudanças nas fórmulas financeiras.
6. Exporte resultado e registre para cada exceção: regra, objeto, severidade,
   justificativa e impacto. Regras inaplicáveis não podem desaparecer sem registro.
7. Salve e execute novamente o parser e a conciliação DAX.

Referências: [BPA](https://docs.tabulareditor.com/onboarding/bpa.html)
e [regras oficiais do Tabular Editor](https://github.com/TabularEditor/BestPracticeRules).

## 12. Evidências e encerramento

Capture telas reais do Desktop após a aprovação dos testes; não gerar mockups.
Salve inicialmente na pasta da sessão e selecione as evidências finais para
`docs/images/powerbi/`:

- `executive.png`, `products.png`, `customers.png`, `channels.png`, `simulator.png`.
- Uma demonstração curta real do simulador (GIF ou vídeo), incluindo mudança de
  desconto e resposta das métricas, sem telas de credenciais.
- Capturas da conexão/refresh e do calendário, sem segredos.
- Layouts mobile e matriz de revisão, com limitações de dispositivo declaradas.
- Resultado BPA e relatório de paridade **desta execução**.

Depois das edições, execute novamente:

```powershell
pwsh -NoProfile -File .\scripts\phase1_powerbi.ps1 -Mode Validate
git diff --stat
git diff -- powerbi
git status --short
```

Atualize `powerbi/validation.md`, `docs/v2-delivery-report.md` e README com versão,
origem realmente testada, período, evidências e pendências resolvidas. Confira os
links. Não copiar outputs contendo dados sensíveis. Artefatos locais são ignorados;
promova somente as evidências revisadas que devem integrar a documentação.

**Definição de pronto:** conexão direta e refresh comprovados; oito totais e quatro
cenários com diferença zero; cinco páginas aprovadas; calendário revisado; filtros,
What-if, teclado e mobile testados; BPA executado com exceções justificadas;
screenshots reais; projeto salvo, reaberto e novamente validado; documentação coerente.
Itens reprovados ou pendentes impedem chamar a fase inteira de concluída.

O script não cria commit nem publica. Ao decidir publicar esta fase, revise o diff,
execute a CI e faça commit/push conforme a autorização vigente para essa entrega.
Não avance para a próxima fase apenas porque Prepare/Validate retornou 0.

## 13. Diagnóstico e recuperação

| Problema | Ação |
|---|---|
| `pwsh` não encontrado | Disponibilizar PowerShell 7 antes de executar; não substituir silenciosamente por 5.1 |
| `.venv` ou dependências ausentes | Seguir `docs/execution.md`; depois repetir Prepare |
| Conexão recusada ao PostgreSQL | Conferir Docker ativo, serviço deste Compose e host/porta; usar StartPostgres se apropriado |
| Erro de autenticação | Conferir credencial local e origem do Desktop; não colocar senha no Git ou em captura |
| Prepare passa, Desktop não atualiza | O conector/Desktop tem sua própria autenticação; validar manualmente a seção 5 |
| Nenhuma porta ativa | Abrir o PBIP, aguardar o modelo carregar e tentar novamente |
| Várias portas | Fechar outros relatórios ou identificar e informar a porta correta |
| Medida DAX não encontrada | Conferir projeto aberto e medidas existentes; não trocar nomes para contornar o erro |
| Diferença financeira | Parar, limpar contexto de comparação, conferir snapshot/refresh e regras de arredondamento; não aumentar tolerância |
| Schema PBIR indisponível | Registrar a revisão e a compatibilidade aplicada; não chamar isso de validação exata |
| Falha após mexer no calendário | Identificar hierarquia usada pelos visuais, corrigir eixos e revisar diff; não apagar dimensões para fazer o parser passar |
| Precisar recuperar arquivos | Fechar o Desktop antes de restaurar arquivos específicos do backup da sessão; revisar o diff e reabrir. Não restaurar pastas inteiras cegamente |

Cada falha gera `result.json` com a etapa reprovada. Corrija a causa e execute uma
nova sessão; não edite o JSON para transformar reprovação em aprovação.
