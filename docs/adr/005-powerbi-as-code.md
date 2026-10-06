# ADR 005 — Power BI versionável e validado no Desktop

Decisão: PBIP, TMDL e PBIR. TOM Microsoft 19.84.1 serializa/valida TMDL; Desktop
Store 2.158.1177.0 abriu, carregou e salvou o projeto. ADOMD consultou o motor local;
oito totais monetários e quatro cenários passaram com diferença zero.
Credenciais não são colocadas nas partições M ou no repositório.

Snapshot CSV permite reprodução local sem autenticação inicial; parâmetro SourceMode
alterna para PostgreSQL. A conexão direta exige credencial no Desktop e verificação
separada. Esses modos não são confundidos no relatório de validação.

Alternativa rejeitada: PBIX fictício/construído por ZIP sem execução real.
PBIX é opcional para release; cache e configurações .pbi ficam fora do Git.
CURRENCY + centavos/basis points substituem aritmética Double nos cenários para
reproduzir HALF_UP. Valores escalados precisam caber na precisão inteira do motor.

Desktop pode gravar revisões PBIR mais novas que os schemas públicos disponíveis;
o verificador registra checks de compatibilidade com versão pública anterior,
sem alterar os arquivos ou alegar validação exata de revisão indisponível.
Execução real no Desktop continua necessária, especialmente após mudanças DAX.
