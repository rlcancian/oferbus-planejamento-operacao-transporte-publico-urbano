# OferBus — Legacy File Format Specification v0.1

**Status:** documentação arqueológica.  
**Importante:** os formatos históricos **não são requisito da arquitetura moderna**. Este documento existe para recuperação de conhecimento, validação e eventual migração única de dados legados para PostgreSQL.

## 1. Decisão vigente

A rematerialização do OferBus não manterá compatibilidade operacional contínua com os arquivos da década de 1990/2000. O fluxo moderno será:

`arquivo legado (eventual) → importação/migração → modelo moderno → PostgreSQL`

Não há requisito de exportar novamente `.OFB`, `.LEV`, `.RST`, `.PRJ` ou formatos equivalentes.

## 2. Manifestos de projeto

### `.OFB`

Funciona como manifesto de um projeto/linha. A seção `ARQUIVOS` referencia componentes associados, incluindo, conforme a geração do projeto:

- cadastro de frota;
- identificação/dados básicos da linha;
- levantamento diário;
- demanda mensal;
- previsão;
- especificações de projeto;
- resultados;
- numeração/programação de veículos;
- restrições/resultados do otimizador.

Os exemplos históricos mostram caminhos relativos e caminhos DOS absolutos. Há também variações de nomenclatura e projetos com extensões duplicadas.

### `.PML`

Manifesto associado ao planejamento multilinha. Referencia elementos como:

- conjunto/cadastro de linhas;
- tripulação;
- jornadas;
- escala;
- deslocamentos entre terminais;
- artefatos de programação multilinha.

## 3. Arquivos associados identificados

A arqueologia encontrou referências/artefatos com extensões como:

- `.IDF` — identificação/dados básicos da linha/frota, conforme versão;
- `.CFR` — cadastro de frota/modelos;
- `.LEV` — levantamento de viagens;
- `.DDM` — demanda mensal;
- `.PRV` — previsão;
- `.PRJ` — especificações/projeto;
- `.RST` — resultados;
- `.NUM` — numeração/programação de veículos;
- `.OTM` — parâmetros/resultados do otimizador;
- `.LIN` — cadastro de linhas em contexto multilinha;
- `.DES` — deslocamentos;
- `.CAD` — cadastro de tripulação;
- `.JOR` — jornadas;
- `.TRI` — escala/tripulação.

A associação exata varia entre versões.

## 4. Natureza física

A investigação do código mostrou dois padrões:

1. arquivos texto/manifesto no estilo INI;
2. arquivos binários gravados com `Open ... For Random` e UDTs do Visual Basic.

Portanto a afirmação antiga de que “os arquivos do OferBus são ASCII” não é válida para todo o sistema. Existe uma camada textual de intercâmbio/documentação, mas boa parte da persistência nativa usa registros binários.

## 5. Versionamento físico observado

Projetos históricos adicionais mostraram tamanhos distintos para arquivos com a mesma extensão, por exemplo:

- `.IDF` com 206, 210 e 234 bytes;
- `.PRJ` com 36 e 40 bytes;
- `.LEV` compatível com registros de tamanhos diferentes entre conjuntos;
- `.NUM` com 180 e 400 bytes.

Conclusão: um único parser baseado exclusivamente nos UDTs do código 2008c não é seguro para toda a história do produto. Qualquer migração futura deverá detectar a geração do formato ou usar heurísticas validadas.

## 6. Estruturas lógicas relevantes

Os formatos refletem diretamente UDTs/globais do legado, entre eles:

- linha e terminais;
- modelos/tipos de veículo;
- levantamento e viagens observadas;
- demanda mensal;
- previsão;
- especificações de projeto;
- viagens planejadas;
- vínculos;
- programação por veículo;
- resultados/indicadores;
- restrições do otimizador;
- funcionários;
- jornadas;
- períodos de escala;
- deslocamentos multilinha.

Na arquitetura moderna essas estruturas não deverão ser reproduzidas como blobs binários. Devem ser normalizadas/estruturadas segundo o domínio reconstruído.

## 7. Riscos de interpretação

- padding/alinhamento dos UDTs pode variar conforme versão/compilador;
- strings fixas do VB podem ocupar comprimentos específicos;
- enums/flags podem ter representação compactada;
- números podem usar tipos VB com tamanhos distintos dos equivalentes modernos;
- índices podem ser 0-based ou 1-based conforme estrutura;
- sentinelas negativas aparecem em dados/curvas;
- ausência de metadado explícito de versão em alguns arquivos;
- caminhos embutidos podem ser absolutos e não portáveis;
- arquivos diferentes podem ter sido gravados por versões distintas do programa.

## 8. Estratégia correta de migração

Se houver interesse em preservar projetos históricos reais:

1. selecionar um conjunto representativo de projetos;
2. identificar versão provável por manifesto, tamanho e contexto;
3. decodificar cada arquivo sem executar código legado;
4. validar campos contra manual, código e coerência interna;
5. transformar para objetos do domínio moderno;
6. executar validações/invariantes;
7. persistir no PostgreSQL;
8. registrar origem, arquivo, hash, parser/versão e data da migração;
9. manter o arquivo original apenas como evidência/arquivo histórico, não como estado operacional.

## 9. Requisitos para um eventual `Legacy Importer`

O importer, se desenvolvido, deve ser:

- ferramenta de migração isolada do runtime principal;
- somente leitura sobre o legado;
- determinístico;
- versionado;
- idempotente quando possível;
- capaz de gerar diagnóstico por campo/registro;
- incapaz de sobrescrever silenciosamente dados modernos;
- acompanhado por hashes dos arquivos de origem;
- coberto por fixtures representativas das diferentes gerações.

Não deve existir dependência permanente da aplicação SaaS/Web em arquivos históricos.

## 10. Relação com PostgreSQL

A estrutura física dos arquivos não deve ditar tabelas. O esquema PostgreSQL será derivado de:

- entidades e value objects do domínio reconstruído;
- invariantes;
- proveniência;
- cenários/versionamento;
- multi-tenancy;
- auditoria;
- necessidades dos motores computacionais.

Campos compactados como `Tipo` e `Vinculos` devem virar propriedades explícitas, enums/flags bem tipados ou relações, mantendo o valor bruto apenas como metadado de importação quando necessário.

## 11. Status

| Item | Estado |
|---|---|
| Manifestos `.OFB/.PML` | CONFIRMADOS |
| Existência de formatos binários VB | CONFIRMADA |
| Associação lógica das principais extensões | CONFIRMADA/PARCIAL conforme versão |
| Versionamento físico entre gerações | CONFIRMADO |
| Packing exato de todas as versões | NÃO NECESSÁRIO PARA O RUNTIME; UNKNOWN para algumas gerações |
| Importação histórica única | OPCIONAL |
| Compatibilidade contínua de arquivos | NÃO REQUERIDA |
| Persistência moderna | PostgreSQL, modelagem ainda a consolidar |
