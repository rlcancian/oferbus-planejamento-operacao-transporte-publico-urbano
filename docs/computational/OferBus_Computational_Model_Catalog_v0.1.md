# OferBus — Computational Model Catalog v0.1

**Status:** catálogo arqueológico dos modelos computacionais recuperados.  
**Objetivo:** impedir perda, reinterpretação ou “modernização” silenciosa da semântica matemática do OferBus.

## Convenções

- **SOURCE-VALIDATED:** reconstruído diretamente do código legado.
- **DOC-VALIDATED:** descrito na documentação histórica.
- **CROSS-VALIDATED:** código e documentação convergem.
- **NUMERIC-GOLDEN-MASTER-PENDING:** sem prova numérica end-to-end suficiente.
- **DIVERGENT:** código e documentação divergem em aspecto relevante.

A regra arquitetural é: primeiro reproduzir o modelo histórico; somente depois corrigir, substituir ou ampliar, sempre em variante separada e versionada.

## Catálogo resumido

| ID | Modelo | Finalidade | Fonte principal | Estado | Plano |
|---|---|---|---|---|---|
| LEG-DMD-001 | Passageiros por minuto | converter viagens observadas em fluxo temporal | `Calcula_Passageiros_Por_Minuto` | SOURCE-VALIDATED | preservar |
| LEG-DMD-002 | Curva original diária | expandir observações para minuto a minuto | `Calcula_Curva_Original` | SOURCE-VALIDATED | preservar |
| LEG-DMD-003 | Ajuste por agregação + média móvel | suavizar demanda/IR/TPV | `Ajusta_Uma_Curva` | SOURCE-VALIDATED | preservar parametrizado |
| LEG-DMD-004 | Conservação de massa | manter total diário após suavização | `Corrige_Curva_Ajustada` | SOURCE-VALIDATED | preservar |
| LEG-DMD-005 | Modelo de demanda variável | usar curva contínua ajustada | pipeline | SOURCE-VALIDATED | preservar |
| LEG-DMD-006 | MPTDC | segmentar o dia em patamares | `Calcula_Periodos_Tipicos` | DIVERGENT | preservar variantes |
| LEG-TT-001 | Curva original de TPV | interpolar tempos observados | `Calcula_Org_Tmp` | SOURCE-VALIDATED | preservar |
| LEG-TT-002 | Ajuste de TPV | suavizar tempo de viagem | `Ajusta_Uma_Curva` | SOURCE-VALIDATED | preservar |
| LEG-TT-003 | TPV expresso | derivar tempo de viagem expresso | pipeline/documentação | CROSS-VALIDATED | preservar |
| LEG-IR-001 | Completar passageiros críticos | preencher observações incompletas | `Completa_Dados_PassageirosCriticos` | SOURCE-VALIDATED | preservar compatibilidade |
| LEG-IR-002 | IR médio constante | usar IR global | `CodIndiceRenova=0` | SOURCE-VALIDATED | preservar |
| LEG-IR-003 | IR variável | construir/ajustar curva de IR | `Calcula_Org_IR` | SOURCE-VALIDATED | preservar + testar |
| LEG-FC-001 | Preparação da série mensal | médias móveis/anuais | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-002 | Previsão para série curta | tratar histórico reduzido | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-003 | Regressão parabólica | previsão mensal | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-004 | Regressão logarítmica | previsão mensal | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-005 | Regressão exponencial | previsão mensal | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-006 | Seleção por DQM | escolher modelo automaticamente | `Previsao_Da_Demanda` | SOURCE-VALIDATED | preservar |
| LEG-FC-007 | Fator previsão→dia típico | escalar demanda diária | `Calcula_Fator_Previsao` | SOURCE-VALIDATED | preservar |
| LEG-CAP-001 | Capacidade por nível de serviço | converter NS em lotação admissível | `Define_Lotacao_No_Onibus` | SOURCE-VALIDATED; defeito candidato | legacy + corrected |
| LEG-TIME-001 | Saída virtual | incorporar tempo de embarque | `Calc_SaidaVirtual` | SOURCE-VALIDATED | preservar |
| LEG-TIME-002 | Chegada virtual | TPV + desembarque | `Calc_ChegadaVirtual` | SOURCE-VALIDATED | preservar |
| LEG-SCH-001 | Máximo robusto | estabilizar pico de referência | `Calcula_Maxi_Por_Medias` | SOURCE-VALIDATED | preservar |
| LEG-SCH-002 | Quadro mínimo 2007 | gerar partidas | `Calcula_Quadro_Horarios_Minimo_2007` | SOURCE-VALIDATED | preservar + caracterizar |
| LEG-SCH-003 | Retorno sem estocagem | manter continuidade operacional | `MMARCHA1` | SOURCE-VALIDATED | preservar |
| LEG-SCH-004 | Ajeitadinha 0/5 | ajustar horários para minutos preferenciais | `Ajeitadinha_Brasileira_Horarios` | SOURCE-VALIDATED | opção explícita |
| LEG-LNK-001 | Vinculação operacional | encadear viagens compatíveis | `MMARCHA1` | SOURCE-VALIDATED | preservar |
| LEG-FLT-001 | Alocação por cadeia | atribuir veículo lógico | programação | SOURCE-VALIDATED | preservar |
| LEG-FLT-002 | Frota efetiva | derivar veículos necessários | resultados | SOURCE-VALIDATED | preservar |
| LEG-FLT-003 | Frota reserva | aplicar percentual de reserva | `Calc_Frota_Reserva` | SOURCE-VALIDATED | preservar |
| LEG-NS-001 | NS por viagem | classificar carga/serviço | `Calcula_NS_Viagem` | SOURCE-VALIDATED | preservar |
| LEG-MET-001 | Indicadores | QDT, PMD, OM, OMTC, IPK, custos etc. | `Calcula_Inform_Resultados` | SOURCE-VALIDATED; auditoria pendente | preservar + revisar |
| LEG-OPT-001 | Busca enumerativa | varrer especificações e filtrar soluções | `Executa_Otimizador` | PARTIAL/evolutivo | `LegacyEnumerativeSearch` |
| LEG-CREW-001 | Verificação de restrições | validar escala | `Verifica_Restricoes_Escala` | SOURCE-VALIDATED/evolutivo | política histórica |
| LEG-CREW-002 | Escala automática 1 | gerar alocação de tripulação | `Escala_Automatica_Algoritmo1` | PARTIAL | reconstruir |
| LEG-CREW-003 | Escala automática 2 | heurística gulosa/memória | `Escala_Automatica_Algoritmo2` | PARTIAL | reconstruir/benchmark |

## Demanda

### LEG-DMD-001 — Passageiros por minuto

Converte contagens por viagem em taxa temporal. Entre partidas, a quantidade observada é distribuída pelo intervalo. Partidas coincidentes recebem tratamento para evitar divisão por zero e preservar o volume.

### LEG-DMD-002 — Curva diária original

Expande as taxas em uma série minuto a minuto. Essa curva é a referência para ajustes posteriores e para conservação do volume diário.

### LEG-DMD-003 — Suavização

`Ajusta_Uma_Curva` executa:

1. agregação em blocos de aproximadamente 10 minutos;
2. cálculo de pontos representativos;
3. média móvel simétrica segundo grau configurado;
4. interpolação linear de volta para resolução de um minuto;
5. tratamento específico de bordas.

A mesma infraestrutura é reaproveitada por demanda, TPV e IR.

### LEG-DMD-004 — Conservação de massa

Após a suavização, `Corrige_Curva_Ajustada` reescala a série quando necessário para reconciliar o total representado com o total diário observado. Índices e arredondamentos históricos devem ser caracterizados antes de qualquer refatoração.

### LEG-DMD-006 — MPTDC

O modelo cria faixas horizontais, usa cruzamentos da curva ajustada como candidatos a fronteiras, elimina períodos muito curtos e atribui a cada período a média da curva original.

Há divergência confirmada:

- Manual 2005: MDV intermediário com grau 3; código 2008c força grau 2.
- Manual: número de faixas = grau; código: `AjustePeriodo * 2`.

Portanto devem existir variantes versionadas, não uma interpretação única arbitrária.

## Tempo de viagem

`Calcula_Org_Tmp` constrói/interpola a curva de TPV observada; depois a infraestrutura comum de ajuste suaviza a série. Há comparação suspeita com `2` em contexto relacionado à sentinela `-2`; isso permanece **candidate defect**, não correção aplicada.

O TPV expresso é tratado separadamente no pipeline legado.

## Índice de renovação

O sistema suporta IR médio constante ou curva variável. Quando faltam passageiros críticos, há rotina para completar os dados. `Calcula_Org_IR` produz a curva temporal e reutiliza a infraestrutura de suavização. Também há comparação suspeita com `2`/`-2`, a ser caracterizada.

## Previsão de demanda

`Previsao_Da_Demanda` contém modelos parabólico, logarítmico e exponencial por mínimos quadrados e tratamento específico para séries curtas. O sistema calcula erro quadrático médio e pode selecionar automaticamente o melhor modelo histórico. `Calcula_Fator_Previsao` converte a previsão mensal em fator para o dia típico.

A modernização futura poderá acrescentar novos modelos, mas os três modelos históricos devem permanecer reproduzíveis como família `legacy`.

## Capacidade e nível de serviço

`Define_Lotacao_No_Onibus` converte nível de serviço em capacidade admissível combinando assentos e área para passageiros em pé.

**BUG-CAND-001:** o código aparenta utilizar `gVeiculoPadrao` mesmo quando outro modelo de veículo está em escopo. O reference core deve manter duas variantes: `legacy` e `corrected`, até validação histórica.

## Horários reais e virtuais

`Calc_SaidaVirtual` desloca a saída real pelo tempo estimado de embarque. `Calc_ChegadaVirtual` combina saída, TPV e tempo de desembarque. Esses horários virtuais participam da compatibilidade operacional entre viagens; não são meros campos de apresentação.

## Quadro mínimo de horários

`Calcula_Quadro_Horarios_Minimo_2007` executa construção minuto a minuto. Em alto nível:

```text
para cada sentido operacional:
    inicializar âncora e acumuladores
    para cada minuto do período:
        acumular demanda
        determinar lotação admissível
        combinar lotação e IR para capacidade efetiva
        se capacidade, intervalo máximo, limite temporal ou retorno exigirem:
            criar viagem
            calcular horários reais/virtuais
            tratar retorno/estocagem
            atualizar acumuladores
garantir extremos operacionais
regularizar partidas finais
opcionalmente aplicar ajuste 0/5
ordenar viagens
```

O algoritmo inclui mais regras do que a formulação conceitual descrita no manual, especialmente retorno, estocagem, âncoras e regularização final.

**BUG-CAND-002:** em um replay de demanda após retorno normal, existe loop em `i` com acesso aparente ao índice `cont`. Deve ser reproduzido/isolado em characterization test antes de decisão.

## Vinculação, programação e frota

Viagens possuem vínculos de entrada e saída. Cadeias compatíveis recebem o mesmo veículo lógico. Uma nova cadeia que não pode reutilizar veículo existente aumenta a frota efetiva. A frota reserva é então derivada por percentual configurado.

A implementação moderna deve representar explicitamente `VehicleBlock`/cadeia operacional em vez de inferir tudo por números compactados.

## Indicadores

`Calcula_Inform_Resultados` produz, entre outros:

- passageiros totais;
- número de viagens;
- frota efetiva;
- quilometragem diária;
- percurso médio por veículo;
- ocupação média;
- ocupação no trecho crítico;
- taxa de ocupação;
- IPK;
- aproveitamento/viagens por veículo;
- custos diário, médio, por viagem e por passageiro;
- tempo médio de viagem;
- velocidade média programada.

**BUG-CAND-005:** `QDT = NV × extensão média` pode divergir de `Σ NV_s × L_s` quando os sentidos possuem números de viagens diferentes. Deve haver variante histórica e auditoria moderna.

## Otimizador

O otimizador legado não deve ser descrito como solver global. Ele enumera combinações discretas de especificações, executa o planejamento e filtra resultados por restrições. Seu status histórico é parcial/evolutivo. O nome proposto para preservação é `LegacyEnumerativeSearch`.

## Escala de tripulação

`Verifica_Restricoes_Escala` distingue múltiplos tipos de violação, incluindo sobreposição, duração, terminal, deslocamento, jornada, intervalos e trocas. Existem pelo menos dois algoritmos automáticos. O segundo executa tentativas e seleção heurística, com memória opcional. Não há evidência de ótimo global.

## Defeitos candidatos registrados

| ID | Local | Hipótese | Estado |
|---|---|---|---|
| BUG-CAND-001 | capacidade | veículo padrão pode ser usado indevidamente | INCERTO |
| BUG-CAND-002 | quadro mínimo | replay usa índice errado | FORTE SUSPEITA |
| BUG-CAND-003 | IR | provável confusão `2`/`-2` | INCERTO |
| BUG-CAND-004 | TPV | provável confusão `2`/`-2` | INCERTO |
| BUG-CAND-005 | indicadores | QDT pode ser semanticamente inadequado | A AUDITAR |
| BUG-CAND-006 | relatórios | histórico registra relatórios desatualizados | RISCO CONFIRMADO |

## Critério de modelo reconstruído

Um modelo só muda para **VALIDATED** quando houver:

1. especificação independente do VB;
2. entradas, unidades, parâmetros e domínio explícitos;
3. fixture controlada;
4. implementação de referência determinística;
5. comparação com resultado histórico ou interpretação manual comprovada;
6. tolerância numérica declarada;
7. casos-limite;
8. decisão explícita sobre defeitos históricos (`reproduce`, `fix`, `parameterize`).

**Estado global:** reconstrução estrutural avançada; paridade numérica completa ainda pendente.
