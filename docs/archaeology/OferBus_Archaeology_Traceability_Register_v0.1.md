# OferBus — Archaeology Traceability Register v0.1

**Objetivo:** manter a cadeia `artefato → conceito → regra → requisito futuro → teste → evidência`, distinguindo convergências e divergências entre código e documentação.

## 1. Registro principal

| TR-ID | Artefato/evidência | Conceito recuperado | Regra/semântica | Estado de evidência | Requisito futuro | Teste de caracterização |
|---|---|---|---|---|---|---|
| TR-001 | `MGLOBAL.BAS:388–411` | Linha | identificação + operação + terminais + extensão + IR + custos + estocagem | código | importar sem perda e normalizar responsabilidades | round-trip de `TpLinha` |
| TR-002 | `MGERAL::Str_Tipo_Operacao` | Tipo de operação | códigos 0..6 com nomenclatura histórica | código | enumeração legacy + modelo moderno explícito | tabela 0..6 |
| TR-003 | `TpViagem` + `.LEV` | Viagem observada | horário, passageiros, trecho crítico, TPV | código | dataset observacional versionado | parser + validação de sentinela |
| TR-004 | Manual §6.2.1 + `Ajusta_Uma_Curva` | MDV | 10 min → média móvel → interpolação | código+doc | `LegacyDemandSmoothing` determinístico | série sintética manualmente calculável |
| TR-005 | `Corrige_Curva_Ajustada` | conservação de demanda | reescala suavização para preservar total | código | manter massa no modo legacy | soma antes/depois |
| TR-006 | Manual §6.2.2 + `Calcula_Periodos_Tipicos` | MPTDC | patamares constantes delimitados por cruzamentos de faixas | código+doc com divergência parametrização | preservar duas fontes e decidir via golden master | casos com 2..9 graus |
| TR-007 | `Calcula_Passageiros_Por_Minuto` | fluxo de passageiros | passageiros/intervalo entre partidas; coincidências tratadas | código | função pura | partidas iguais e distintas |
| TR-008 | `Calcula_Org_Tmp`/ajuste | TPV | interpolação + suavização | código | modelo legacy versionado | pontos esparsos e bordas |
| TR-009 | `Completa_Dados_PassageirosCriticos` | compatibilidade IR | reconstrói trecho crítico ausente | código | migrar levantamentos antigos | `.LEV` antigo sem PTC |
| TR-010 | `CodIndiceRenova` + curvas | IR | médio constante ou variável | código | seleção explícita de modelo | fixtures constante/variável |
| TR-011 | Manual §previsão + `Previsao_Da_Demanda` | previsão | parábola, exponencial, log e seleção por mínimos quadrados | código+doc | preservar modelos históricos | séries com solução conhecida |
| TR-012 | `Calcula_Fator_Previsao` | dia típico previsto | previsão mensal × participação / levantamento | código | provenance de escalonamento | cálculo escalar simples |
| TR-013 | `Define_Lotacao_No_Onibus` | capacidade/NS | assentos + 1,5×área livre×nível | código; bug candidato | `LegacyCapacityModel` + modelo corrigido separado | 2 modelos distintos |
| TR-014 | Manual §7.1.3 | quadro mínimo | maximizar intervalos sujeito a demanda/IR/lotação e ITVmax | documentação | preservar intenção matemática | comparar formulação com algoritmo |
| TR-015 | `Calcula_Quadro_Horarios_Minimo_2007` | quadro mínimo implementado | varredura minuto a minuto e gatilhos de partida | código | implementação legacy independente da UI | golden master de linha |
| TR-016 | Manual §7.1.4 + `FMARCH04` | edição profissional | criar/excluir/mover/deslocar/trocar tipo/vínculo/TPV | código+doc | comandos de domínio + auditoria | E2E por comando |
| TR-017 | Manual §7.1.4 + `Calc_*Virtual` | horário virtual | inclui embarque/desembarque além dos tempos reais | código+doc | dual timeline explícita | fórmula e toggle visual |
| TR-018 | `TpObjViagem.Tipo` + editores | proveniência da viagem | bit field de expresso/criação/importação/overrides | código | decompor em campos semânticos | todas as combinações usadas |
| TR-019 | `Vinculos`, `Seta_Vinculo` | vínculo | entrada/saída compactadas; garagem/estocagem/operação | código | `TripLink` estruturado | encode/decode round-trip |
| TR-020 | Manual §7.1 + `MMARCHA1` | viagens de retorno | equilibram terminais/frota em linhas de 2 terminais | código+doc | preservar geração e distingui-la de viagens manuais | cenário pico assimétrico |
| TR-021 | Manual §7.1.4 | comportamento após edição | por default não recria retornos; refaz vínculos para respeitar edição | documentação + flags de código | override não sobrescrito silenciosamente | editar/excluir retorno e recalcular |
| TR-022 | programação/vínculos | veículo/bloco | cadeias de viagens determinam veículo | código+doc | `VehicleBlock` explícito | cobertura sem conflito |
| TR-023 | `Calcula_Inform_Resultados` | indicadores | FE, QDT, PMD, OM, IPK, custos etc. | código | catálogo de métricas versionado | fórmula a fórmula |
| TR-024 | `FRMOTIMI` + histórico 2006/07 | otimizador | enumeração + filtros; implementação historicamente incompleta | código+histórico | `LegacyEnumerativeSearch`, não solver genérico | espaço pequeno enumerável |
| TR-025 | `TpFuncionario`, `TpJornada` | tripulação | cadastro + policy histórica de jornada | código | regras versionadas/jurisdição | validação por regra |
| TR-026 | `FGRAFESC::Verifica_Restricoes_Escala` | restrições de escala | códigos específicos de conflito | código | diagnósticos estruturados | um fixture por violação |
| TR-027 | `Escala_Automatica_Algoritmo1/2` | geração de escala | heurísticas automáticas, algoritmo 2 com memória opcional | código | legacy crew engine isolado | fixture pequeno exaustivamente verificável |
| TR-028 | `.OFB` + `Load/Save_Projeto_Da_Linha` | projeto | manifesto de arquivos especializados | código | importer seguro | projeto histórico completo |
| TR-029 | `.PML` + `MESCALA3` | multilinha | manifesto de linhas/tripulação/jornadas/deslocamentos | código+histórico | extensão multilinha sem alegar completude histórica | projeto com ≥2 linhas |
| TR-030 | histórico 2008 | multilinha/crew | mecanismos incorporados em 2008 | histórico+código | maturidade marcada `partial/evolving` | testes separados por feature |
| TR-031 | histórico 2006 | relatórios | alguns relatórios declarados desatualizados | histórico | reconstruir conteúdo a partir dos cálculos, não copiar cegamente | comparação com dados-base |
| TR-032 | `ofbdlgs` Delphi | infraestrutura | helper para limitações Win16/diálogos/licença | código | não transportar para domínio | N/A |

## 2. Divergências código × documentação que exigem decisão explícita

### DIV-001 — Grau base usado pelo MPTDC

**DOCUMENTAÇÃO (Manual 2005 §6.2.2):** antes da segmentação em períodos típicos, aplicar MDV com **Grau de Ajustamento 3**.  
**CÓDIGO (`MPROCEDI.BAS:1473–1489`):** quando MPTDC está ativo, salva o grau atual e força `AjusteDemDiaria(1/2) = 2` durante o alisamento.

**Status:** DIVERGÊNCIA CONFIRMADA. Não escolher silenciosamente um dos dois. Um golden master de projeto MPTDC deve determinar qual comportamento era observado na versão de 2005/2008; versões diferentes podem precisar de engines distintas.

### DIV-002 — Número de faixas do MPTDC

**DOCUMENTAÇÃO:** número `n` de faixas corresponde ao Grau de Ajustamento, variando de 2 a 9.  
**CÓDIGO (`MGERAL.BAS:1778–1782`):** `numFaixas(sent) = AjustePeriodo(sent) * 2`.

**Status:** DIVERGÊNCIA CONFIRMADA. A UI persiste diretamente valores mínimos 2 (`FESPPRO3.FRM:1199–1212`), e `alfa()` apenas converte o número para texto, portanto não há evidência de que o valor armazenado seja índice disfarçado. Prioridade alta para golden master.

### DIV-003 — Formulação matemática versus algoritmo executado do quadro mínimo

**DOCUMENTAÇÃO (Manual §7.1.3):** formula o problema como maximização de `ITVi = Hi − Hi-1`, sujeito à capacidade/demanda/IR e intervalo máximo.  
**CÓDIGO (`Calcula_Quadro_Horarios_Minimo_2007`):** implementação construtiva minuto a minuto, com regras adicionais de terminais, retorno, ancoragem nas viagens levantadas e pós-processamento dos últimos intervalos.

**Status:** NÃO necessariamente contraditório. O manual parece expressar o objetivo/restrições conceituais; o código implementa uma heurística/construção operacional mais detalhada. A equivalência matemática não foi provada.

### DIV-004 — Afirmação documental de minimização de frota/custo

**DOCUMENTAÇÃO (Manual §7.1.4):** afirma que o modelo matemático “minimiza a frota efetiva e o custo de operação”.  
**CÓDIGO recuperado:** há heurísticas explícitas para criação/vinculação de retornos e alocação; não foi localizado nesta passagem um solver global que prove minimização simultânea de custo/frota no planejamento de linha.

**Status:** DOCUMENTED CLAIM, IMPLEMENTATION PROOF NOT YET RECOVERED. Não promover essa frase a garantia matemática da rematerialização sem demonstrar equivalência/ótimo.

## 3. Defeitos candidatos prioritários

| BUG-ID | Fonte | Observado | Hipótese | Evidência necessária |
|---|---|---|---|---|
| BC-001 | `MPROCEDI:549–568` | lê modelo solicitado em `numAss/AreaLivre`, mas calcula com `gVeiculoPadrao` | modelo não padrão ignorado | caso com dois modelos + saída histórica |
| BC-002 | `MMARCHA1:184–188` | `For i=...`, soma `CurvaAjustada(sentido, cont)` | índice incorreto no replay | fixture com curva não constante |
| BC-003 | `MPROCEDI:102,108,112` | escreve/testa `-2`, mas teste final é `=2` | typo de sinal | caso em que último ponto é sentinela |
| BC-004 | `MPROCEDI:162,168,172` | padrão idêntico para TPV | typo de sinal | idem |
| BC-005 | `Calcula_Inform_Resultados` | QDT baseada em `NV × L_médio` | erro quando viagens por sentido diferem | comparar com soma por sentido |

## 4. Gate de evidência

Para os itens críticos TR-004 a TR-027, a cadeia só será considerada fechada quando houver:

`fonte legado → especificação independente → fixture → execução de referência → resultado esperado → comparação automatizada → decisão sobre divergências/bugs`.

No estado atual, a **arqueologia semântica está avançada**, mas a **paridade numérica ainda é UNKNOWN** por ausência de projetos nativos e resultados históricos correspondentes no pacote.
