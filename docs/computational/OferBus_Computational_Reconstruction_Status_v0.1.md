# OferBus — Computational Reconstruction Status v0.1

## Decisão de escopo

Os formatos históricos `.OFB/.LEV/.RST/...` não são requisito de compatibilidade do OferBus moderno. Eles passam a ser tratados apenas como fontes arqueológicas e, se útil, como entrada de uma migração única. A persistência operacional futura será relacional, com PostgreSQL como hipótese aprovada pelo usuário. Nenhum design moderno deve reproduzir limitações dos formatos legados.

## Objetivo desta etapa

Converter algoritmos já confirmados no código Visual Basic em funções pequenas, determinísticas e testáveis, independentes de UI e persistência. O pacote Python criado é um **harness científico de caracterização**, não uma decisão sobre a linguagem final do planning engine.

## Implementado

| Modelo | Estado | Evidência |
|---|---|---|
| LEG-DMD-001 Passageiros/minuto | IMPLEMENTADO | port direto de `Calcula_Passageiros_Por_Minuto` |
| LEG-DMD-002 Curva original | IMPLEMENTADO | port direto de `Calcula_Curva_Original` |
| LEG-DMD-003 Ajuste da curva | IMPLEMENTADO | port direto de `Ajusta_Uma_Curva` |
| LEG-DMD-004 Conservação de massa | IMPLEMENTADO | port direto de `Corrige_Curva_Ajustada` |
| LEG-SCH-001 Máximo robusto | IMPLEMENTADO | port direto de `Calcula_Maxi_Por_Medias` |
| LEG-CAP-001 Capacidade | IMPLEMENTADO em duas variantes | `legacy` preserva BUG-CAND-001; `corrected` usa o veículo solicitado |
| LEG-FLT-003 Frota reserva | IMPLEMENTADO | preserva arredondamento histórico estrito `> .5` |
| LEG-FC-003/004/005/006 | IMPLEMENTADO parcialmente | ramo com >=3 períodos anuais completos: parabólico, logarítmico, exponencial e seleção por DQM |
| LEG-TIME-001/002 | IMPLEMENTADO | saída/chegada virtual com dependências antes globais tornadas explícitas |

## Testes

`python -m pytest` → **9 passed**.

Os testes atuais são **source-derived characterization fixtures**. Eles demonstram que a implementação satisfaz contratos extraídos do fonte, mas ainda não constituem golden masters obtidos pela execução de um binário histórico.

## Decisões importantes preservadas

1. Arredondamento histórico: `Int(x)` seguido de incremento apenas quando a parte fracionária é **estritamente maior** que `0.5`; portanto `2.5 -> 2`, não 3.
2. `LEG-CAP-001`: o comportamento histórico aparentemente usa sempre `gVeiculoPadrao`; não foi corrigido silenciosamente.
3. Tempos virtuais agora recebem curvas, capacidades e máximo como argumentos explícitos, eliminando estado global sem alterar a fórmula.
4. O port usa estruturas modernas e não reproduz arrays fixos de 400/1440 como invariantes de domínio; apenas preserva a semântica algorítmica relevante.

## Próxima tranche de reconstrução

Prioridade alta:

1. `Calcula_Org_Tmp` e `Calcula_Org_IR`, com variantes que reproduzem e corrigem o provável teste de sentinela `2` versus `-2`;
2. `LEG-DMD-006` períodos típicos, preservando separadamente a variante `code-2008c` e a semântica descrita no Manual 2005;
3. completar `Previsao_Da_Demanda`: ramo de 1–2 anos, sazonalidade/`MesesEscolhidos` e `Calcula_Fator_Previsao`;
4. reconstruir `Calcula_Quadro_Horarios_Minimo_2007` em funções menores;
5. caracterizar a suspeita `CurvaAjustada(sentido, cont)` versus `CurvaAjustada(sentido, i)` no replay após retorno;
6. reconstruir vinculação e alocação de veículos;
7. só então consolidar indicadores e custos.

## Gate

- Núcleo computacional inicial: **PASS**.
- Testabilidade isolada: **PASS**.
- Paridade com fonte por inspeção/port: **PASS parcial**.
- Golden master histórico executável: **UNKNOWN / não requerido para prosseguir**.
- Planning engine completo: **FAIL / ainda incompleto**.
- Persistência PostgreSQL moderna: **não iniciada nesta etapa**.
