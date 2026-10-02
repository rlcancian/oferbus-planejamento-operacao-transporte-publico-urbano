# OferBus — Phase B.4 Plan / Result Persistence v0.1

**Status:** CONCLUÍDA  
**Data:** 2026-10-02

## Objetivo

Materializar como fonte de verdade PostgreSQL o resultado operacional produzido por `core-planning`, preservando uma linhagem imutável e reconstruível:

```text
ScenarioRevision
→ ComputationRun
→ PlanRevision
→ PlannedTrip
→ VehicleBlock / VehicleBlockTrip
→ ResultSnapshot
```

A B.4 não introduz edição de horários nem interface operacional. Ela cria a base persistente e consultável que será consumida pela B.5 e, posteriormente, pelo Gráfico de Marcha editável.

## Separação entre plano e resultado

Dois conceitos são persistidos separadamente:

- `PlanRevision` representa uma revisão do plano operacional. A revisão computada aponta para o `ComputationRun`; o modelo já admite futura revisão manual por `parent_plan_revision_id` e `source_kind=manual`.
- `ResultSnapshot` representa as métricas calculadas para uma revisão específica do plano.

Essa separação evita tratar métricas derivadas como parte estrutural do horário e permite que a Phase C crie novas revisões do plano sem sobrescrever o plano que lhes deu origem.

## Migration `0005_planning_results`

A migration adiciona cinco tabelas:

### `plan_revision`

Preserva:

- organização;
- `ScenarioRevision` de origem;
- `ComputationRun` gerador, quando computado;
- revisão pai;
- número imutável da revisão;
- origem `computed` ou `manual`;
- semantic layer;
- `engine_id` e `engine_version`;
- input/output fingerprints.

### `planned_trip`

Persiste cada movimento operacional em ordem de pipeline:

- sentido e número legado do sentido;
- partida/chegada reais em minutos de serviço;
- partida/chegada virtuais;
- tipo da viagem;
- flag expressa;
- bloco/veículo atribuído;
- nível de serviço.

`vehicle_block_no=0` é permitido para representar explicitamente uma viagem ainda não vinculada; blocos reais continuam numerados a partir de 1.

### `vehicle_block`

Persiste a identidade do bloco/veículo, quantidade de viagens e limites temporais observados no bloco.

### `vehicle_block_trip`

Persiste a ordem exata das viagens dentro de cada bloco. Essa tabela é propositalmente relacional: ela prepara a futura edição do Gráfico de Marcha sem exigir interpretação de um JSON opaco.

### `result_snapshot`

Persiste todos os campos atuais de `PlanningMetricsResult`, além de output fingerprint e notas de provenance.

## Fidelidade numérica

Os contratos atuais do `oferbus-core` representam métricas calculadas como `float` Python. A B.4 persiste esses valores como PostgreSQL `double precision` (`Float` em SQLAlchemy), em vez de `NUMERIC(p,s)`.

A decisão é deliberada: quantizar valores em seis ou oito casas poderia alterar o material reconstruído e quebrar o `output_fingerprint`. Se uma versão futura do core promover custos ou outras métricas para `Decimal`, o tipo físico deverá evoluir junto com o contrato científico, explicitamente.

## Fingerprint canônico de resultado

O cálculo do fingerprint foi centralizado no próprio `oferbus-core`:

- `planning_result_payload(result)`;
- `planning_result_fingerprint(result)`.

O payload material inclui semantic layer, engine, input fingerprint, viagens, frota, ordenação dos blocos, métricas e provenance. O próprio `output_fingerprint` é excluído do payload para permitir verificação recursivamente estável.

O `ReferencePlanningAdapter` e a reconstrução PostgreSQL usam a mesma função. Portanto não existem duas implementações independentes da identidade de um resultado.

## Fronteira de persistência

`packages/oferbus-planning/results.py` implementa:

```text
persist_planning_result(...)
load_planning_result(...)
```

Antes de gravar, a aplicação verifica:

1. fingerprint material do resultado;
2. `run_kind=core-planning`;
3. input fingerprint do run;
4. semantic layer;
5. identidade e versão do engine;
6. consistência da frota e dos blocos;
7. índices de viagens referenciados pelos blocos;
8. unicidade de atribuição de viagem a bloco.

A gravação de `PlanRevision`, viagens, blocos e snapshot ocorre em uma transação.

## Idempotência e recuperação de worker

Existe no máximo um `PlanRevision` computado por `ComputationRun`.

Se o worker conseguir persistir o plano e cair antes de executar `queue.succeed(...)`, uma nova tentativa encontra a revisão já gravada. Ela somente é reutilizada se fingerprints, semantic layer e provenance do engine coincidirem exatamente; em seguida o resultado é reconstruído e validado.

Assim uma falha entre `COMMIT do resultado` e `COMMIT do estado succeeded` não duplica planos nem substitui dados existentes.

## Reconstrução como verificação de integridade

`load_planning_result(...)` não devolve as linhas cegamente. Ele reconstrói um `PlanningResult` completo e verifica:

- fingerprint de `PlanRevision` versus `ResultSnapshot`;
- quantidade de viagens;
- identidade e ordem dos blocos;
- atribuição das viagens;
- `planning_result_fingerprint(reconstruído)` igual ao fingerprint original.

Uma divergência gera `PlanningResultIntegrityError` em vez de retornar um resultado parcialmente confiável.

## Worker

O handler `core-planning` agora segue:

```text
load/verify input
→ execute core
→ verify result
→ persist immutable result
→ reload/verify persisted result
→ queue.succeed
```

Progresso atual:

- 10% — job aceito;
- 35% — input carregado/verificado;
- 85% — core concluído;
- 95% — resultado persistido e reconstruído;
- 100% — execução marcada `succeeded`.

Os percentuais identificam fronteiras operacionais e não estimam tempo restante.

## API

A API `0.8.0` adiciona:

```text
GET /results/computations/{run_id}
```

A consulta exige `result:read` e retorna:

- IDs do run, `PlanRevision` e `ResultSnapshot`;
- número da revisão do plano;
- semantic layer e engine;
- fingerprints;
- quadro de viagens;
- blocos com ordem das viagens;
- frota efetiva;
- métricas operacionais e de custo;
- notas de provenance.

A resposta é produzida somente após reconstrução e verificação do fingerprint persistido.

## Quality gate

O smoke integrado com PostgreSQL 18 prova:

```text
migration 0005
→ deterministic seed
→ core-planning
→ PlanRevision
→ PlannedTrip
→ VehicleBlock / VehicleBlockTrip
→ ResultSnapshot
→ GET /results/computations/{run_id}
→ reconstrução do PlanningResult
→ mesmo output_fingerprint
```

O gate também mantém regressão da fronteira assíncrona e do Copilot da Phase A.

## Fora do escopo

A B.4 não implementa:

- edição manual do plano;
- comparação visual entre revisões;
- Gráfico de Marcha;
- frontend de timetable/blocos/métricas;
- otimização;
- escala de tripulação.

A próxima subfase, B.5, consome esta API para construir o primeiro workspace operacional do OferBus no navegador.
