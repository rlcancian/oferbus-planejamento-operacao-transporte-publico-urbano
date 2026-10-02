# OferBus — Phase B.3 Deterministic Planning Worker v0.1

**Status:** CONCLUÍDA  
**Data:** 2026-10-02

## Objetivo

Transformar a fronteira assíncrona criada na Phase A em uma execução real de planejamento OferBus, sem antecipar a persistência detalhada de resultados da B.4.

O novo fluxo é:

```text
POST /computations
→ ScenarioRevision imutável
→ PlanningInput reconstruído e verificado
→ ComputationRun(core-planning)
→ fila PostgreSQL
→ worker
→ ReferencePlanningAdapter / oferbus-core
→ fingerprints + diagnóstico técnico
→ ComputationRun succeeded
```

## Handler `core-planning`

O worker possui agora dois handlers:

- `platform-smoke` — mantido exclusivamente como regressão da infraestrutura assíncrona;
- `core-planning` — primeira execução determinística real do núcleo de planejamento.

O handler de planejamento:

1. verifica se o engine esperado pelo job coincide com o engine carregado pelo worker;
2. exige `input_fingerprint` no `ComputationRun`;
3. carrega o `PlanningInput` usando `packages/oferbus-planning`;
4. recalcula e compara o fingerprint do snapshot imutável;
5. compara a semantic layer persistida com a semantic layer enfileirada;
6. executa `ReferencePlanningAdapter`;
7. confere novamente provenance do engine e input fingerprint retornados pelo core;
8. registra `output_fingerprint` no `ComputationRun`;
9. grava somente um resumo diagnóstico técnico nesta fase;
10. conclui o job com progresso 100%.

## Fronteira da API

A API `0.7.0` aceita:

```json
{
  "scenario_revision_id": "<uuid>",
  "run_kind": "core-planning",
  "idempotency_key": "..."
}
```

Para `core-planning`, parâmetros científicos ad-hoc no payload são rejeitados. O backend deriva da revisão imutável:

- semantic layer;
- input fingerprint;
- engine descriptor.

Um cliente pode informar `semantic_layer` apenas como asserção redundante; se ela divergir da revisão persistida, a submissão é rejeitada.

A resposta de `POST /computations` e `GET /computations/{run_id}` passa a incluir:

- `scenario_revision_id`;
- `engine_version`;
- `input_fingerprint`;
- `output_fingerprint` quando concluído.

## Reprodutibilidade

O descritor atual do engine executado pela B.3 é formado por:

```text
reference-bridge:<ENGINE_VERSION>
```

O worker se recusa a executar um job cujo descritor esperado seja diferente do engine disponível no processo. Isso impede que um worker antigo ou incompatível produza silenciosamente um resultado com provenance incorreta.

O `input_fingerprint` é fixado no momento do enqueue e verificado novamente no worker. O `output_fingerprint` é produzido pelo `oferbus-core` e persistido apenas após sucesso.

## Idempotência endurecida

A reutilização de uma `idempotency_key` dentro da mesma organização só é aceita quando a identidade material do cálculo coincide. São comparados:

- scenario revision;
- run kind;
- semantic layer;
- engine version/source revision;
- deterministic seed;
- input fingerprint;
- payload.

Reutilização conflitante gera `IdempotencyConflictError` e HTTP 409 em vez de retornar silenciosamente outro cálculo.

## Retry policy

Falhas determinísticas conhecidas são não-retryable:

- snapshot ausente ou inconsistente;
- fingerprint divergente;
- semantic layer divergente;
- engine incompatível;
- erro determinístico de validação/cálculo do core.

Falhas inesperadas da fronteira de infraestrutura permanecem retryable e seguem a política limitada da fila PostgreSQL.

## Progresso

`core-planning` atualiza heartbeat/progresso em três fronteiras:

- 10% — job aceito pelo worker;
- 35% — snapshot carregado e validado;
- 85% — cálculo concluído e em validação/finalização;
- 100% — `queue.succeed(...)` persistido.

Esses valores representam estágios operacionais, não estimativa matemática de tempo restante.

## O que é persistido na B.3

No `ComputationRun`:

- engine version;
- semantic layer;
- input fingerprint;
- output fingerprint;
- status/timestamps;
- resumo diagnóstico com quantidade de viagens, frota efetiva, passageiros, distância, custo e notas de provenance.

O resumo em `diagnostics` **não é o resultado operacional autoritativo**. Ele serve para observabilidade e prova de execução.

## Explicitamente fora do escopo

A B.3 não persiste ainda:

- timetable detalhado;
- viagens planejadas como entidades de domínio;
- vínculos;
- blocos de veículos;
- snapshots completos de métricas/resultados.

Essa linhagem pertence à B.4:

```text
ComputationRun
→ PlanRevision
→ PlannedTrip / links / blocks
→ ResultSnapshot / metrics
```

## Quality gate

O integrated smoke agora prova em PostgreSQL 18 real:

```text
migrations
→ deterministic seed
→ API/worker startup
→ planning input API round-trip
→ Phase A platform-smoke regression
→ POST core-planning
→ immutable input verification
→ real oferbus-core execution
→ succeeded
→ output fingerprint persisted
```

Também verifica que o cálculo produz pelo menos uma viagem e uma frota efetiva positiva na fixture determinística de desenvolvimento.
