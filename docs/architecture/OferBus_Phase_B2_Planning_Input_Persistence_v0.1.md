# OferBus — Phase B.2 Planning Input Persistence v0.1

**Status:** CONCLUÍDA  
**Data:** 2026-10-02

## Objetivo

Materializar a persistência e a fronteira de aplicação necessárias para transformar dados observados e parâmetros de planejamento em um `PlanningInput` imutável, tenant-safe e verificável pelo `oferbus-core`.

## Modelo persistido

A migration `0004_planning_inputs` adiciona:

- `observed_trip_dataset` — conjunto lógico reutilizável de dados observados por linha;
- `observed_trip_dataset_revision` — revisão imutável, numerada, com fingerprint de conteúdo e proveniência;
- `observed_trip_observation` — viagens observadas por sentido e ordem de origem;
- `scenario_planning_input` — snapshot dos parâmetros gerais de uma `ScenarioRevision`;
- `scenario_direction_planning_input` — snapshot por sentido: dataset revision, curvas, janela de serviço, extensão e parâmetros operacionais.

As referências críticas usam `organization_id` em foreign keys compostas para impedir associação entre organizações diferentes no próprio banco.

## Fronteira de aplicação

`packages/oferbus-planning` é a camada compartilhada entre API e, na próxima subfase, worker. Ela depende de `oferbus-db` e `oferbus-core`, mas não de FastAPI.

Responsabilidades atuais:

1. criar dataset observado e sua primeira revisão;
2. criar revisões imutáveis posteriores do mesmo dataset;
3. criar uma nova `ScenarioRevision` de planejamento;
4. carregar observações da revisão de dataset selecionada;
5. montar exatamente os contratos tipados do `oferbus-core`;
6. validar o input científico;
7. calcular o SHA-256 canônico do `PlanningInput`;
8. persistir o fingerprint em `ScenarioRevision`;
9. reconstruir o input posteriormente e rejeitar divergência de fingerprint.

O `oferbus-core` continua sem dependência de PostgreSQL, HTTP ou worker.

## API

A API `0.6.0` expõe:

```text
POST /planning/datasets
POST /planning/datasets/{dataset_id}/revisions
POST /planning/scenario-revisions
GET  /planning/scenario-revisions/{scenario_revision_id}/input
```

Permissões:

- datasets e revisões de datasets: `project:write`;
- criação de revisão de cenário: `scenario:write`;
- leitura do input congelado: `scenario:read`.

Entradas semanticamente inválidas retornam erro de cliente. A camada `modern` permanece não implementada no motor e não é tratada como capacidade disponível.

## Fixture de desenvolvimento

O seed determinístico agora inclui uma linha operacional mínima baseada na fixture de caracterização já existente:

- um sentido `outbound`;
- janela de serviço de 60 a 120 minutos;
- três viagens observadas;
- extensão de 8 km;
- curvas determinísticas de demanda, IR e tempo de viagem;
- veículo de referência;
- custo por quilômetro;
- semantic layer `normalized`.

Depois de persistir, o seed usa `load_planning_input(...)` e recalcula o fingerprint. Qualquer divergência aborta o seed.

## Quality gate

O integrated smoke aplica todas as migrations em PostgreSQL 18, executa o seed e consulta o input pela API autenticada. Ele verifica:

- migration `0004_planning_inputs`;
- organização correta;
- `ScenarioRevision` de planejamento recuperável;
- semantic layer `normalized`;
- sentido esperado;
- três observações;
- fingerprint SHA-256 válido;
- manutenção do smoke assíncrono e da fronteira de IA da Phase A.

## Fora do escopo desta subfase

B.2 não executa ainda o planejamento real no worker e não persiste timetable/resultados calculados. Esses itens pertencem respectivamente às subfases B.3 e B.4.
