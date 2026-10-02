# OferBus — Feature Parity Matrix v0.1

**Objetivo:** contrato inicial de paridade funcional entre legado e futura rematerialização.  
**Regra:** `Paridade obrigatória` significa preservar a capacidade/semântica, não copiar a UI nem necessariamente reproduzir defeitos fora do modo legacy-compatible.

| ID | Funcionalidade | Evidência principal | Estado legado | Paridade obrigatória | Redesign | Teste futuro mínimo |
|---|---|---|---|---|---|---|
| F-001 | Cadastro de identificação da linha | `TpLinha`, `FLINHA2` | completa | sim | forte | round-trip de campos + validação |
| F-002 | Tipos de operação Circular/Radial/etc. | `Str_Tipo_Operacao` | completa | sim | moderado | 7 códigos e sentidos ativos |
| F-003 | Terminais por linha | `TpLinha.Terminal` | completa | sim | moderado | persistência e uso no planejamento |
| F-004 | Extensão por sentido | `TpLinha.Extensao` | completa | sim | leve | indicadores com sentidos distintos |
| F-005 | Área de estocagem por terminal | `TpLinha.AreaEstocagem` | completa | sim | leve | geração com/sem estocagem |
| F-006 | Cadastro de modelos de veículo | `TModeloVeiculo`, `FFROTA` | completa | sim | moderado | capacidade e quantidade |
| F-007 | Restrições/números de veículo | `.NUM`, `TpRestricVeic` | completa/evolutiva | sim | moderado | import/export + alocação |
| F-008 | Levantamento de viagens diário | `TpViagem`, `FVIAGENS` | completa | sim | forte | dataset com 1/2 sentidos |
| F-009 | Passageiros transportados por viagem | `NumPassageiros` | completa | sim | leve | curva diária |
| F-010 | Passageiros no trecho crítico | `NumPassCritico` | completa tardia | sim | leve | IR variável |
| F-011 | Tempo de viagem observado | `TempoViagem` | completa | sim | leve | interpolação TPV |
| F-012 | Metadados de dia típico | `TpLevantamento` | completa | sim | moderado | D.U./sábado/feriado |
| F-013 | Demanda mensal até 60 meses | `TpDemanda` | completa | sim | forte | série datada + import legado |
| F-014 | Previsão parabólica | `Previsao_Da_Demanda` | completa | sim legacy | nenhum no core | golden master |
| F-015 | Previsão logarítmica | idem | completa | sim legacy | nenhum no core | golden master |
| F-016 | Previsão exponencial | idem | completa | sim legacy | nenhum no core | golden master |
| F-017 | Seleção automática de previsão | DQM em `Previsao_Da_Demanda` | completa | sim legacy | moderado | reproduzir seleção |
| F-018 | Ajuste/suavização de demanda | `Ajusta_Uma_Curva` | completa | sim | nenhum no core | curva fixture |
| F-019 | Conservação do total ajustado | `Corrige_Curva_Ajustada` | completa | sim | nenhum no core | soma pré/pós |
| F-020 | Demanda variável | pipeline | completa | sim | nenhum | golden master |
| F-021 | Períodos típicos de demanda constante | `Calcula_Periodos_Tipicos` | completa | sim | UI forte | segmentação fixture |
| F-022 | Ajuste do tempo de viagem | curva TPV | completa | sim | nenhum no core | curva fixture |
| F-023 | IR médio | `CodIndiceRenova=0` | completa | sim | nenhum | fixture |
| F-024 | IR variável | `CodIndiceRenova=1` | completa | sim | nenhum | fixture + missing values |
| F-025 | Especificações de projeto | `TpEspecProjeto`, `FESPPRO3` | completa | sim | forte | versionamento cenário |
| F-026 | Nível de serviço | capacidade/`NS` | completa | sim | forte | A–F e limites |
| F-027 | Nível de vale | `NivelVale` | completa | sim | leve | impacto em capacidade |
| F-028 | Intervalo máximo | `IntervaloMax` | completa | sim | leve | gatilho de partida |
| F-029 | Retorno normal/expresso | `CriaExpresso` | completa | sim | moderado | terminal sem estocagem |
| F-030 | Quadro de horários mínimo | `Calcula_Quadro_Horarios_Minimo_2007` | completa | sim crítica | UI forte, core não | golden master E2E |
| F-031 | “Ajeitadinha” horários 0/5 | rotina específica | completa | sim como opção legacy | redesign conceitual | comparação on/off |
| F-032 | Tempos reais/virtuais | `Calc_*Virtual` | completa | sim crítica | explicação UI | fórmula + limites |
| F-033 | Gráfico de marcha | `FMARCH04` | completa/central | sim crítica | total | testes de interação + invariantes |
| F-034 | Zoom no gráfico de marcha | `FMARCH04` | completa | sim capacidade | total | viewport |
| F-035 | Seleção/multisseleção de viagens | `FMARCH04` | completa | sim | total | interação E2E |
| F-036 | Criar viagem manual | `Cria_Viagem_Projetista` | completa | sim | total | provenance + recálculo |
| F-037 | Excluir viagem | `Apaga_Viagem` | completa | sim | total | undo + restrições |
| F-038 | Alterar horário | `Altera_Horario_Viagem` | completa | sim | total | dependências recalculadas |
| F-039 | Deslocar grupo de viagens | `Desloca_Viagens` | completa | sim | total | múltiplas viagens |
| F-040 | Alterar tipo normal/expresso | `Troca_Tipo_Viagem` | completa | sim | total | bitfield/proveniência |
| F-041 | Alterar vínculos | `FVINCUL`, `FMARCH04` | completa | sim | total | entrada/saída independentes |
| F-042 | Vincular garagem | `Vinc_*Gar*` | completa | sim | total | cadeia e frota |
| F-043 | Vincular estocagem | `Vinc_*Estoc*` | completa | sim | total | cadeia e frota |
| F-044 | Undo no gráfico | `Acao_Desfaca` | completa | sim | total | command history |
| F-045 | Redo no gráfico | `Acao_Refaca` | completa | sim | total | command history |
| F-046 | Informações de viagem | `Info_Viagem`, `FINFVIA2` | completa | sim | forte | painel consistente |
| F-047 | Visualização real/virtual | `FMARCH04` | completa | sim | forte | toggle sem alterar dados |
| F-048 | Vinculação automática de viagens | `MMARCHA1` | completa | sim crítica | nenhum no core | golden master |
| F-049 | Programação por veículo | `FPROGRAC` | completa | sim crítica | total | blocos + cobertura 100% |
| F-050 | Alocação automática de veículos | rotinas de programação | completa | sim crítica | nenhum no core | cadeias fixture |
| F-051 | Frota efetiva | resultados | completa | sim | moderado | contagem de blocos |
| F-052 | Frota reserva | `PorcentFrotaReserva` | completa | sim | leve | arredondamento |
| F-053 | Lotação projetada | `FGRAFLOT` | completa | sim | forte | curva e NS |
| F-054 | Oferta levantada | `FGRFOFER`/relatórios | completa | sim | forte | série |
| F-055 | Oferta projetada | idem | completa | sim | forte | série |
| F-056 | Demanda × oferta | gráficos/relatórios | completa | sim | forte | alinhamento temporal |
| F-057 | Indicadores operacionais | `Calcula_Inform_Resultados` | completa | sim crítica | forte | fórmula por fórmula |
| F-058 | Custos por km | `TipoCusto`/resultados | completa | sim legacy | forte | unidade e cenário |
| F-059 | Custos fixos + variáveis | idem | completa | sim legacy | forte | fórmula fixture |
| F-060 | Comparação de alternativas | projeto/resultados/UI | completa | sim | total | cenário A/B imutável |
| F-061 | Relatórios de entrada/resultados | `FRELATO4`, histórico | parcial/desatualizado em partes | seletiva | total | conteúdo sem layout legado |
| F-062 | Impressão legada | VBX/Crystal/printing | obsoleta | não visual | substituir | PDF/web print |
| F-063 | Exportação de relatórios para arquivo | histórico 2006 | completa | sim capacidade | total | export determinístico |
| F-064 | Projeto `.OFB` | `Load/Save_Projeto_Da_Linha` | completa | sim para migração | importer | round-trip de manifesto |
| F-065 | Importação/exportação TXT | `MARQUIV4` | parcial por tipo | sim para formatos úteis | redesign | fixtures por extensão |
| F-066 | Projeto multilinha `.PML` | `MESCALA3`, 2008 | parcial/evolutivo | sim após definição | total | integração 2+ linhas |
| F-067 | Cadastro de linhas multilinha | `FLINHAS`, `.LIN` | parcial/evolutivo | sim | total | lista 2+ linhas |
| F-068 | Tempos de deslocamento entre terminais | `.DES` | parcial/evolutivo | sim se usado pela escala | total | matriz coerente |
| F-069 | Compartilhamento/remanejamento entre linhas | 2008/escala | parcial | sim como capacidade futura | total | caso multilinha |
| F-070 | Cadastro de tripulação | `FCADTRIP`, `TpFuncionario` | substancial | sim | total + LGPD | CRUD + autorização |
| F-071 | Políticas/jornadas | `FJORNADA`, `TpJornada` | substancial | sim como legacy policy | total | regras versionadas |
| F-072 | Escala gráfica de tripulação | `FGRAFESC` | substancial/evolutiva | sim | total | edição + validação |
| F-073 | Escala automática algoritmo 1 | `FGRAFESC` | parcial/evolutiva | sim legacy se reproduzível | nenhum core | golden master |
| F-074 | Escala automática algoritmo 2 | `FGRAFESC` | parcial/evolutiva | sim legacy se reproduzível | nenhum core | benchmark + fixture |
| F-075 | Verificação de restrições da escala | `Verifica_Restricoes_Escala` | substancial | sim | regras externalizadas | cada código de violação |
| F-076 | Motorista + cobrador por viagem | `TpObjViagem` | implementado | sim legacy | configurável | cobertura |
| F-077 | Duplas de funcionários | `TpFuncionario.IDDupla` | implementado | seletiva | configurável | alocação dupla |
| F-078 | Otimizador de projeto | `FRMOTIMI`, histórico | parcial | sim como legacy search, não como única otimização | total UI | reproduzir enumeração |
| F-079 | Restrições do otimizador | `.OTM` | implementada | sim legacy | forte | filtros determinísticos |
| F-080 | Licenciamento EVERLOCK/serial | fontes auxiliares | obsoleto | não | remover deliberadamente | N/A |
| F-081 | Auxiliar Delphi para diálogos/serial | `ofbdlgs` | infraestrutura legada | não | remover | N/A |
| F-082 | Dependência de VBX | `.MAK` | obsoleta | não | substituir | N/A |
| F-083 | Associação de extensão no Windows | histórico 2007 | infraestrutura | não | substituir por import web | N/A |
| F-084 | Editor/visualizador de arquivos legado | `FFILEDI2` | utilitário | seletiva | substituir | preview/import diagnostics |
| F-085 | Relato de inconformidade/bug | histórico 2007, `FBUG` | implementado | capacidade equivalente | total | observabilidade/support bundle |
| F-086 | Conversores externos configuráveis | `TpRotinaConversao` | incerto | desconhecida | investigar | contrato externo |
| F-087 | Ajuda/manual integrado | arquivos/help | legado | conteúdo sim, mecanismo não | total | documentação navegável |
| F-088 | Golden-master reproduzível | não há dataset suficiente no pacote | NÃO RECUPERADO | requisito novo obrigatório | N/A | fixture + resultado conhecido |

## Classificação de risco para paridade

### Tier A — patrimônio computacional/operacional

`F-018..060`: curvas, previsão, planejamento, gráfico de marcha, vínculos, programação por veículo, frota e indicadores. Perda ou alteração silenciosa aqui descaracterizaria o OferBus.

### Tier B — extensões tardias a preservar com maturidade explícita

`F-066..079`: multilinha, tripulação e otimizador. Devem ser reconstruídos, mas sem declarar completude superior à evidência histórica.

### Tier C — infraestrutura obsoleta a remover deliberadamente

`F-062`, `F-080..083`: impressão/controle ActiveX/VBX, licença EVERLOCK, helper Delphi e associações de arquivo Windows. A paridade é de **capacidade**, quando ainda relevante, não de mecanismo.

## Critério de aceite atual

- Cobertura inicial de funcionalidades: **PASS**.
- Maturidade classificada para subsistemas centrais: **PASS**.
- Prova de paridade numérica: **UNKNOWN/PENDING**.
- Prova de paridade de interação gráfica: **UNKNOWN/PENDING** até execução/referências visuais completas e testes E2E futuros.
