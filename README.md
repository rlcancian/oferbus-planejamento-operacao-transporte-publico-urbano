# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência possui caracterização executável, o modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A **Phase A — Platform Foundation** está concluída e foi validada tanto no GitHub Actions quanto no notebook de desenvolvimento: PostgreSQL 18, migrations, seed, FastAPI, worker, Next.js e smoke integrado estão operacionais.

A **Phase B — Core Planning Vertical Slice** está em andamento:

- **B.1 — Production Planning Contracts and Reference Bridge:** concluída;
- **B.2 — Planning Input Persistence and Application Boundary:** concluída;
- **B.3 — Deterministic Planning Worker:** concluída;
- **B.4 — Plan and Result Persistence:** concluída;
- **B.5 — Web Planning Result Workspace:** concluída;
- **B.6 — Integrated Acceptance and Regression Gate:** próxima.

## Arquitetura aceita

- Next.js 16 + React 19 + TypeScript no frontend;
- FastAPI/Python como backend autoritativo de aplicação;
- OferBus Core Python independente, determinístico e versionado;
- PostgreSQL como fonte de verdade;
- SQLAlchemy + Alembic + psycopg na camada de persistência Python;
- fila inicial de jobs apoiada em PostgreSQL, acessada por uma abstração `JobQueue`;
- workers Python com lease, heartbeat, retry, idempotência e progresso por SSE;
- SVG/D3 para engenharia 2D e Three.js/React Three Fiber para visualizações 3D quando agregarem valor;
- OferBus Copilot/Planning Agent como componente nativo, provider-neutral e sempre operando por ferramentas estruturadas, permissões e confirmações;
- monólito modular, não microserviços prematuros.

## Vertical slice de planejamento

`packages/oferbus-core` contém contratos tipados, semantic layers, validação e fingerprints determinísticos. A ponte `ReferencePlanningAdapter` executa apenas rotinas arqueológicas já caracterizadas sob esse contrato de produção.

A B.2 introduziu `packages/oferbus-planning` e a migration `0004_planning_inputs`, persistindo datasets observados e snapshots imutáveis de `ScenarioRevision`. Toda leitura recalcula o SHA-256 canônico do `PlanningInput`.

A B.3 conectou esses snapshots à execução assíncrona real por `run_kind=core-planning`. O worker valida semantic layer, input fingerprint e engine antes de executar o core; `ComputationRun` registra input/output fingerprints e provenance.

A B.4 introduziu a migration `0005_planning_results` e tornou o resultado operacional autoritativo no PostgreSQL:

```text
ScenarioRevision
→ ComputationRun
→ PlanRevision
→ PlannedTrip
→ VehicleBlock / VehicleBlockTrip
→ ResultSnapshot
```

`PlanRevision` é separado de `ResultSnapshot` para permitir futuras revisões manuais sem sobrescrever o histórico computado. A ordem das viagens nos blocos é relacional, preparando a Phase C e o Gráfico de Marcha. O resultado persistido é reconstruído pelo `packages/oferbus-planning` e só é aceito se reproduzir exatamente o `output_fingerprint` calculado pelo `oferbus-core`.

A B.5 transformou a raiz do Next.js no primeiro workspace operacional do OferBus. O frontend consome somente a API autoritativa e apresenta contexto de projeto/cenário/linha, timetable, blocos de veículo, frota, demanda, ocupação, custos e provenance. Estados sem resultado ou com infraestrutura indisponível são exibidos explicitamente; nenhum dado é inventado no frontend.

A API `0.9.0` expõe resultados verificados em:

```text
GET /results/computations/{run_id}
GET /results/latest
```

`legacy-exact` e `normalized` são distinguidos explicitamente. `modern` permanece indisponível até existir um modelo moderno real; a plataforma não simula capacidades ainda não implementadas.

## Fundação multiusuário e Copilot

A persistência inclui organizações/usuários, memberships, municípios/operadores/terminais, linhas/sentidos, projetos, cenários/revisões, `ComputationRun`, auditoria, fila, inputs versionados e resultados operacionais imutáveis. Relações tenant-owned críticas usam foreign keys compostas com `organization_id`.

A autenticação possui fronteira substituível; o desenvolvimento usa um adaptador local explicitamente proibido em produção. A aplicação resolve uma organização ativa e aplica RBAC (`owner`, `admin`, `planner`, `viewer`).

A fronteira de IA existe em `packages/oferbus-ai`. Nenhum LLM tem acesso direto a SQL. O provider ainda está deliberadamente `unconfigured`; ferramentas disponíveis são allow-listed, herdam as permissões do usuário e ações de cálculo/mutação exigem confirmação. O cálculo `core-planning` existe de forma determinística, mas ainda não foi exposto como ferramenta do Copilot.

## Execução local

Depois de atualizar `main`:

```bash
make bootstrap
make postgres-up
make migrate
make seed
make doctor
make dev
```

Abra `http://127.0.0.1:3010`.

Se já existir um resultado persistido, a página inicial abre diretamente o workspace operacional. Caso contrário, o estado vazio indica que ainda é necessário executar `core-planning`.

Em outro terminal, com os serviços ativos:

```bash
make smoke
```

O smoke integrado inclui planejamento real, persistência relacional, reconstrução pelo mesmo output fingerprint e descoberta do resultado mais recente com contexto de projeto/cenário/linha.

## Estrutura

- `apps/web/` — aplicação Next.js e workspace operacional;
- `apps/api/` — API FastAPI;
- `apps/worker/` — worker Python para computações longas e planejamento determinístico;
- `packages/oferbus-ai/` — contratos de provider LLM e ferramentas estruturadas do Copilot;
- `packages/oferbus-core/` — contratos e motor computacional de produção;
- `packages/oferbus-db/` — persistência SQLAlchemy/PostgreSQL;
- `packages/oferbus-jobs/` — contrato e implementação da fila assíncrona;
- `packages/oferbus-planning/` — fronteira de aplicação para inputs e resultados de planejamento;
- `reference-core/` — implementação arqueológica executável e testes de caracterização;
- `migrations/` — migrations Alembic;
- `infra/dev/` — infraestrutura local opcional;
- `scripts/` — bootstrap, seed, smoke e diagnóstico local;
- `docs/` — arqueologia, domínio, computação, persistência, decisões e arquitetura.

## Princípios

- preservar separadamente `legacy-exact`, `normalized` e `modern`;
- PostgreSQL é persistência moderna; arquivos históricos são apenas evidência/migração eventual;
- IA interpreta e orquestra, mas não inventa resultados nem escreve SQL diretamente;
- alterações manuais e ações da IA são comandos auditáveis;
- cenários, execuções, planos e resultados são versionados para reprodutibilidade;
- o Gráfico de Marcha permanece um instrumento de engenharia preciso;
- visual moderno e 3D complementam, mas não prejudicam, a precisão operacional.

Consulte `docs/README.md` e `docs/architecture/OferBus_Phase_B_Core_Planning_Vertical_Slice_Plan_v0.1.md` para o estado técnico detalhado.
