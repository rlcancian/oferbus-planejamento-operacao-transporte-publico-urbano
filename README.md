# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência possui caracterização executável, o modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A **Phase A — Platform Foundation** está concluída e foi validada tanto no GitHub Actions quanto no notebook de desenvolvimento: PostgreSQL 18, migrations, seed, FastAPI, worker, Next.js e smoke integrado estão operacionais.

A **Phase B — Core Planning Vertical Slice** também está concluída e validada ponta a ponta.

A **Phase C — March Diagram and Versioned Operational Editing** está em andamento:

- **C.1 — March Read Model and Read-only SVG Surface:** concluída;
- **C.2 — Versioned Editing Domain and Persistence Boundary:** próxima;
- **C.3 — Time Editing and Operational Conflict Validation:** pendente;
- **C.4 — Trip and Block/Link Editing:** pendente;
- **C.5 — Dependent Result Recalculation and Comparison:** pendente;
- **C.6 — Undo/Redo, Audit, Acceptance and Density Gate:** pendente.

## Arquitetura aceita

- Next.js 16 + React 19 + TypeScript no frontend;
- FastAPI/Python como backend autoritativo de aplicação;
- OferBus Core Python independente, determinístico e versionado;
- PostgreSQL como fonte de verdade;
- SQLAlchemy + Alembic + psycopg na camada de persistência Python;
- fila inicial de jobs apoiada em PostgreSQL, acessada por uma abstração `JobQueue`;
- workers Python com lease, heartbeat, retry, idempotência e progresso por SSE;
- SVG semântico como tecnologia inicial do Gráfico de Marcha 2D; Canvas permanece opção condicionada a benchmark de densidade;
- Three.js/React Three Fiber reservado para visualizações 3D quando agregarem valor;
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

`PlanRevision` é separado de `ResultSnapshot` para permitir futuras revisões manuais sem sobrescrever o histórico computado. A ordem das viagens nos blocos é relacional. O resultado persistido é reconstruído pelo `packages/oferbus-planning` e só é aceito se reproduzir exatamente o `output_fingerprint` calculado pelo `oferbus-core`.

A B.5 transformou a raiz do Next.js no primeiro workspace operacional do OferBus. O frontend consome somente a API autoritativa e apresenta contexto de projeto/cenário/linha, timetable, blocos de veículo, frota, demanda, ocupação, custos e provenance. Estados sem resultado ou com infraestrutura indisponível são exibidos explicitamente; nenhum dado é inventado no frontend.

A B.6 fechou a fatia com golden master determinístico e um gate CI que executa planejamento real, persiste/reconstrói o resultado, inicia o Next.js em modo de produção e valida semanticamente o workspace renderizado.

## Gráfico de Marcha

A C.1 recuperou o Gráfico de Marcha como superfície real do workspace. A API `0.10.0` expõe um read model tenant-safe em:

```text
GET /plans/{plan_revision_id}/march
```

O read model inclui revisão/pai/origem, semantic layer, fingerprint, domínio temporal, sentidos, linha, terminais, horários reais/virtuais, tipo, expresso, bloco e nível de serviço.

A interface renderiza um SVG semântico com eixo horizontal de tempo, trilhos de terminais e trajetórias das viagens. Horários virtuais distintos aparecem separadamente; blocos têm distinção visual; e cada viagem continua identificável por número, sentido e tooltip, sem depender apenas de cor.

A C.1 é deliberadamente somente leitura. Nenhuma operação gráfica altera o plano computado. A C.2 introduzirá a fronteira de comandos e revisões manuais derivadas antes de qualquer drag-and-drop.

A API também mantém:

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

Se já existir um resultado persistido, a página inicial abre diretamente o workspace operacional, incluindo o Gráfico de Marcha C.1. Caso contrário, o estado vazio indica que ainda é necessário executar `core-planning`.

Em outro terminal, com os serviços ativos:

```bash
make smoke
```

O smoke é repetível e inclui planejamento real, persistência relacional, reconstrução pelo mesmo output fingerprint, descoberta do resultado mais recente e validação do read model do Gráfico de Marcha.

## Estrutura

- `apps/web/` — aplicação Next.js, workspace operacional e Gráfico de Marcha SVG;
- `apps/api/` — API FastAPI, incluindo resultados e read model da marcha;
- `apps/worker/` — worker Python para computações longas e planejamento determinístico;
- `packages/oferbus-ai/` — contratos de provider LLM e ferramentas estruturadas do Copilot;
- `packages/oferbus-core/` — contratos e motor computacional de produção;
- `packages/oferbus-db/` — persistência SQLAlchemy/PostgreSQL;
- `packages/oferbus-jobs/` — contrato e implementação da fila assíncrona;
- `packages/oferbus-planning/` — fronteira de aplicação para inputs e resultados de planejamento;
- `reference-core/` — implementação arqueológica executável e testes de caracterização;
- `migrations/` — migrations Alembic;
- `infra/dev/` — infraestrutura local opcional;
- `scripts/` — bootstrap, seed, smoke, aceitação web e diagnóstico local;
- `docs/` — arqueologia, domínio, computação, persistência, decisões e arquitetura.

## Princípios

- preservar separadamente `legacy-exact`, `normalized` e `modern`;
- PostgreSQL é persistência moderna; arquivos históricos são apenas evidência/migração eventual;
- IA interpreta e orquestra, mas não inventa resultados nem escreve SQL diretamente;
- alterações manuais e ações da IA são comandos auditáveis;
- cenários, execuções, planos e resultados são versionados para reprodutibilidade;
- o Gráfico de Marcha permanece um instrumento de engenharia preciso;
- visual moderno e 3D complementam, mas não prejudicam, a precisão operacional;
- qualquer edição operacional futura deriva uma nova `PlanRevision`; resultados computados históricos permanecem imutáveis.

Consulte `docs/README.md`, `docs/architecture/OferBus_Phase_B6_Integrated_Acceptance_and_Regression_v0.1.md` e `docs/architecture/OferBus_Phase_C_March_Diagram_and_Versioned_Editing_Plan_v0.1.md` para o estado técnico detalhado.
