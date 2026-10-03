# OferBus — Legacy System Archaeology Report v0.2

**Status:** relatório arqueológico consolidado.  
**Data-base da análise:** 2026-10-01/02.  
**Fonte primária:** pacote legado `OferBus.tar.xz`, especialmente `VERSAO ATUAL/ofb_code/ofb2008c`, documentação histórica e manual do usuário.  
**Regra:** este documento descreve o legado. Não fixa a arquitetura moderna nem transforma hipóteses em fatos.

## Convenções de evidência

- **CONFIRMADO NO CÓDIGO** — comportamento/estrutura recuperado diretamente do fonte.
- **CONFIRMADO NA DOCUMENTAÇÃO** — descrito no manual, PDF ou histórico.
- **CONFIRMADO NO CÓDIGO E NA DOCUMENTAÇÃO** — evidência convergente.
- **INFERIDO** — conclusão técnica forte, porém não declarada literalmente.
- **RELATADO PELO USUÁRIO** — informação fornecida pelo autor, ainda não verificada nos artefatos.
- **INCERTO** — evidência parcial, ambígua ou conflitante.
- **NÃO RECUPERADO** — esperado/mencionado, mas ainda não localizado.

## A. Visão geral

**CONFIRMADO NO CÓDIGO E NA DOCUMENTAÇÃO.** O OferBus é um sistema de planejamento operacional de linhas de transporte coletivo urbano, não apenas um gerador de horários. O pipeline recuperado transforma dados observados e especificações de serviço em curvas de demanda/tempo/IR, previsão opcional, oferta requerida, quadro de horários, gráfico de marcha, vínculos operacionais, programação por veículo, frota, indicadores/custos e comparação de alternativas. Versões posteriores acrescentaram multilinha e escala de tripulação em estágio ainda evolutivo.

O ponto central do sistema é `MPROCEDI.BAS::Make_Urban_Line_Project`, comentado no próprio código como **“CORAÇÃO DO OFERBUS”**.

## B. Arquitetura legada

O pacote contém 201 arquivos. A tecnologia dominante é Visual Basic clássico Win16. O uso de `.MAK`, `.VBX` e APIs Win16 demonstra Visual Basic 3 ou anterior; a hipótese dominante é VB3. Há também um auxiliar Delphi 7 (`ofbdlgs`) usado principalmente para diálogos modernos/compatibilidade e identificação/licenciamento.

O projeto ativo referencia 73 forms, 18 módulos `.BAS` e 12 componentes `.VBX`. Entre as dependências históricas estão `THREED.VBX`, `GRID.VBX`, `CMDIALOG.VBX`, `GRAPH.VBX`, `CRYSTAL.VBX`, `PICCLIP.VBX`, `ofbprn.dll` e DLLs EVERLOCK. Essas dependências não são requisitos da rematerialização moderna.

Módulos centrais recuperados:

- `MGLOBAL.BAS` — tipos e estado global;
- `MGERAL.BAS` — coordenação geral e resultados;
- `MPROCEDI.BAS` — modelos matemáticos e pipeline;
- `MMARCHA1.BAS` — quadro de horários, retornos e vínculos;
- `MARQUIV4.BAS` — persistência/conversões;
- `MFUNCOES.BAS` — funções auxiliares e tempos virtuais;
- `MRELATO2.BAS` / `MRELARQ.BAS` — relatórios;
- `MMULTLIN.BAS` — multilinha;
- `MESCALA3.BAS` / `FGRAFESC.FRM` — tripulação e escala.

Há variantes históricas e código não pertencente à build ativa, portanto presença no diretório não implica funcionalidade da versão final.

## C. Modelo de domínio legado

Conceitos confirmados incluem linha, empresa/cidade, tipos de operação, sentidos, terminal, garagem/estocagem, levantamento, viagem observada, passageiros transportados, passageiros no trecho crítico, demanda mensal, previsão, índice de renovação, tempo de viagem, tipo de veículo, frota, especificações de projeto, viagem planejada, vínculos, programação, resultados, custos, funcionários, jornadas, escalas e deslocamentos multilinha.

`TpObjViagem` é especialmente importante. `Tipo` é um **bit field** com semântica de expresso, origem automática/manual/importada e alterações manuais. `Vinculos` compacta separadamente origem e destino: indefinido, garagem, área de estocagem ou continuidade operacional. Na rematerialização esses valores devem virar propriedades explícitas; o valor bruto só interessa à arqueologia/migração.

## D. Pipeline de planejamento recuperado

A sequência efetivamente recuperada é, em termos conceituais:

1. carregar/cadastrar dados básicos da linha e frota;
2. carregar levantamento diário e demanda mensal;
3. construir curvas originais de demanda, tempo de viagem e IR;
4. ajustar/suavizar curvas;
5. opcionalmente aplicar previsão;
6. definir especificações, nível de serviço, capacidade e intervalo máximo;
7. gerar quadro mínimo de horários;
8. criar viagens e retornos;
9. calcular horários reais e virtuais;
10. ordenar e vincular viagens;
11. construir/editar gráfico de marcha;
12. atribuir cadeias a veículos;
13. determinar frota efetiva e reserva;
14. calcular indicadores e custos;
15. permitir intervenção manual e recálculo;
16. comparar alternativas;
17. em módulos posteriores, integrar multilinha e tripulação.

## E. Modelos matemáticos

Foram identificados e catalogados:

- passageiros por minuto;
- curva diária original;
- agregação em janelas e médias móveis;
- conservação da massa da demanda;
- modelo de demanda variável;
- períodos típicos de demanda constante (MPTDC);
- curva/ajuste do tempo de viagem;
- índice de renovação médio e variável;
- previsão mensal por modelos parabólico, logarítmico e exponencial;
- seleção de previsão por erro quadrático médio;
- fator de previsão para o dia típico;
- capacidade por nível de serviço;
- tempos de saída/chegada reais e virtuais;
- máximo robusto usado no planejamento;
- quadro mínimo de horários;
- retornos em terminais sem estocagem;
- heurística de ajuste para horários terminados em 0/5 (“Ajeitadinha”);
- vinculação de viagens;
- alocação por cadeia e frota;
- indicadores operacionais/econômicos;
- busca enumerativa do otimizador;
- heurísticas/restrições da escala de tripulação.

## F. Gráfico de Marcha

**CONFIRMADO NO CÓDIGO E NA DOCUMENTAÇÃO.** É um editor operacional, não uma visualização passiva. Representa tempo, sentidos, viagens, vínculos, terminais, garagem/estocagem e veículos. O usuário pode alterar viagens e vínculos e essas mudanças repercutem no planejamento. A versão web deverá preservar essa semântica e o caráter editável; a tecnologia gráfica ainda não está fixada.

## G. Programação por veículo e frota

A frota deriva das cadeias de viagens compatíveis. Viagens vinculadas compartilham número lógico de veículo; quando uma cadeia não pode ser continuada, cria-se novo veículo lógico. A frota reserva é calculada separadamente por percentual configurado. A programação, portanto, não deve ser tratada como simples atributo manual de cada viagem.

## H. Tripulação

A escala é **substancial, porém historicamente evolutiva**. Há funcionários, jornadas, períodos, custos, intervalos, deslocamentos, restrições, verificação automática, programação por funcionário e pelo menos dois algoritmos automáticos/heurísticos. Existem `TODO`s e evidências de evolução. Regras trabalhistas históricas deverão ser preservadas somente como política legada; a versão moderna deverá parametrizar regras e validar legislação vigente separadamente.

## I. Planejamento multilinha

Há projeto `.PML`, cadastro de múltiplas linhas, deslocamentos entre terminais e integração com veículos/tripulação. O suporte é real, mas **parcial/em evolução**. A arquitetura moderna não deve assumir um único projeto = uma única linha.

## J. Otimizador

O otimizador 2006–2008 é uma **busca enumerativa** sobre combinações discretas de parâmetros. Para cada combinação executa o planejamento e filtra resultados por restrições como custo, frota, ocupação e quantidade de viagens. Não há evidência suficiente para classificá-lo como solver global com função objetivo única. O comportamento deve ser preservado como `LegacyEnumerativeSearch`; algoritmos modernos de otimização deverão ser componentes separados.

## K. Persistência histórica

Os arquivos legados são agora considerados **evidência arqueológica e possível fonte de migração única**, não contrato futuro. `.OFB`/`.PML` funcionam como manifestos de associação; vários arquivos associados usam registros binários do VB e existem variações entre gerações. A persistência moderna será em banco de dados, com PostgreSQL como hipótese principal já registrada em ADR. Não existe requisito de exportar novamente os formatos históricos.

## L. Relatórios e visualizações

Foram identificadas visualizações para demanda diária/mensal, séries/previsões, tempo de viagem, IR, lotação, oferta, demanda × oferta, programação por veículo, gráfico de marcha e escala. Há relatórios de entradas, horários, programação por veículo, funcionários, indicadores, custos e comparações. O histórico registra que alguns relatórios ficaram desatualizados em determinadas versões; portanto cada relatório deve ser validado contra os cálculos, não copiado cegamente.

## M. Divergências código × documentação

### MPTDC

- Manual 2005: MDV intermediário com grau 3.
- Código 2008c: força temporariamente grau 2.

Além disso:

- Manual: número de faixas = grau de ajustamento (2–9).
- Código: `numFaixas = AjustePeriodo * 2`.

Classificação: **DIVERGÊNCIA CONFIRMADA**. A proveniência do resultado deverá incluir a versão/semântica do algoritmo.

### Quadro mínimo

O manual apresenta a intenção matemática como maximização dos intervalos sob restrições de demanda/capacidade/IR/intervalo máximo. A implementação tardia executa construção minuto a minuto e inclui regras adicionais de retorno, estocagem, ancoragem e regularização. A equivalência formal ainda não está demonstrada.

### Minimização de frota/custo

O manual afirma minimização de frota e custo. O código confirma mecanismos heurísticos orientados à redução de frota, mas não foi demonstrado solver global com prova de otimalidade simultânea.

## N. Defeitos candidatos

Estão registrados como **hipóteses a testar**, nunca como correções automáticas:

1. `Define_Lotacao_No_Onibus` aparenta usar `gVeiculoPadrao` mesmo quando outro modelo está em escopo;
2. em `Calcula_Quadro_Horarios_Minimo_2007`, um replay de demanda itera `i` mas acessa índice `cont`;
3. `Calcula_Org_IR` e `Calcula_Org_Tmp` têm comparações suspeitas com `2` em contextos relacionados à sentinela `-2`;
4. `QDT = NV × extensão média` pode divergir da soma por sentido quando o número de viagens difere;
5. o histórico registra relatórios desatualizados em versões intermediárias.

Cada item exige characterization test antes de decidir `reproduce`, `fix` ou `parameterize`.

## O. Dependências/obsolescência

Não devem ser reutilizados como arquitetura moderna: VBX, APIs Win16, EVERLOCK, Crystal Reports legado, impressão via DLL proprietária, executáveis auxiliares de compressão, WinHelp e integrações por automação antiga. O valor preservável está no domínio e nos algoritmos.

## P. Funcionalidades particularmente valiosas

Não devem ser perdidas:

- cadeia completa demanda → oferta → horários → marcha → veículos → frota;
- representação real/virtual do tempo operacional;
- intervenção manual com consequências recalculadas;
- gráfico de marcha editável;
- comparação explícita de alternativas;
- proveniência de especificações/algoritmos;
- programação por veículo derivada de vínculos;
- capacidade de evoluir para multilinha e tripulação;
- separação entre algoritmo histórico e modelos modernos.

## Q. UNKNOWNs remanescentes

- paridade numérica end-to-end de todos os modelos;
- comportamento exato de algumas variantes históricas;
- semântica completa de todos os relatórios;
- correção dos defeitos candidatos;
- estado final de algumas rotinas multilinha/tripulação;
- critérios precisos de ótimo global, quando alegados pela documentação.

## R. Viabilidade

**PASS — alta viabilidade técnica.** O conhecimento central do sistema está suficientemente recuperado para reconstrução computacional independente da UI. O risco principal não é mais “entender o que o OferBus fazia”, mas garantir paridade matemática e explicitar versões, divergências e correções.

## S. Próxima etapa

A próxima fase é **Computational Reconstruction**:

1. implementar algoritmos como funções/módulos determinísticos independentes da UI;
2. criar fixtures sintéticas e, quando possível, golden masters;
3. versionar variantes `manual-2005`, `code-2008c` e `corrected-modern` onde necessário;
4. caracterizar TPV, IR, MPTDC, quadro mínimo, retornos, vínculos e frota;
5. somente depois congelar a arquitetura de produção e o esquema PostgreSQL definitivo.

## Status por área

| Área | Estado |
|---|---|
| Domínio central | PASS |
| Curvas de demanda/TPV/IR | PASS estrutural |
| Previsão | PASS estrutural |
| Quadro mínimo | PASS estrutural; characterization em andamento |
| Gráfico de marcha | PASS estrutural avançado |
| Programação/frota | PASS estrutural |
| Tripulação | PARTIAL avançado |
| Multilinha | PARTIAL |
| Otimizador | PARTIAL/evolutivo |
| Persistência moderna | decisão: banco de dados; formatos históricos não são requisito |
| Paridade numérica completa | UNKNOWN/PENDING |
