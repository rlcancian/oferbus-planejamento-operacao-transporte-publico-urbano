# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência possui caracterização executável, o modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A **Phase A — Platform Foundation** está concluída e foi validada tanto no GitHub Actions quanto no notebook de desenvolvimento: PostgreSQL 18, migrations, seed, FastAPI, worker, Next.js e smoke integrado estão operacionais.

A **Phase B — Core Planning Vertical Slice** está em andamento:

- **B.1 — Production Planning Contracts and Reference Bridge:** concluída;
- **B.2 — Planning Input Persistence and Application Boundary:** concluída;
- **B.3 — Deterministic Planning Worker:** próxima;
- **B.4 — Plan and Result Persistence:** pendente;
- **B.5 — Web Planning Result Workspace:** pendente;
- **B.6 — Integrated Acceptance and Regression Gate:** pendente.

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

## Núcleo computacional e inputs de planejamento

`packages/oferbus-core` contém os primeiros contratos estáveis de planejamento: entradas/saídas tipadas, unidades operacionais explícitas, semantic layers, validação e fingerprints determinísticos.

A B.1 introduziu `ReferencePlanningAdapter`, uma ponte temporária e explicitamente rastreável sobre rotinas já caracterizadas de `reference-core`. O encadeamento coberto atualmente é:

```text
minimum timetable
→ operational trip attributes
→ basic link graph
→ vehicle blocks / effective fleet
→ service level
→ occupancy
→ operating and cost metrics
```

A B.2 introduziu `packages/oferbus-planning`, a fronteira compartilhada de aplicação entre API e futuro worker. A migration `0004_planning_inputs` persiste datasets observados com revisões imutáveis, observações por sentido e snapshots completos de `ScenarioRevision` com curvas, parâmetros, veículo, custos, semantic layer e fingerprint.

A leitura de um snapshot recalcula o SHA-256 canônico do `PlanningInput`; divergências entre o estado persistido e o fingerprint da revisão são rejeitadas.

`legacy-exact` e `normalized` são distinguidos explicitamente. `modern` permanece indisponível até existir um modelo moderno real; a plataforma não simula capacidades ainda não implementadas.

## Fundação multiusuário e Copilot

A baseline física inclui organizações/usuários, memberships, municípios/operadores/terminais, linhas/sentidos, projetos, cenários/revisões, `ComputationRun`, auditoria, metadados de execução assíncrona e agora inputs de planejamento versionados. As relações tenant-owned críticas usam foreign keys compostas com `organization_id` para impedir referências cruzadas entre organizações no próprio banco.

A autenticação possui fronteira substituível; o desenvolvimento usa um adaptador local explicitamente proibido em produção. A aplicação resolve uma organização ativa e aplica RBAC (`owner`, `admin`, `planner`, `viewer`).

A fronteira de IA existe em `packages/oferbus-ai`. Nenhum LLM tem acesso direto a SQL. O provider ainda está deliberadamente `unconfigured`; ferramentas disponíveis são allow-listed, herdam as permissões do usuário e ações de cálculo/mutação exigem confirmação na baseline atual.

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

Em outro terminal, com os serviços ativos:

```bash
make smoke
```

## Estrutura

- `apps/web/` — aplicação Next.js;
- `apps/api/` — API FastAPI;
- `apps/worker/` — worker Python para computações longas;
- `packages/oferbus-ai/` — contratos de provider LLM e ferramentas estruturadas do Copilot;
- `packages/oferbus-core/` — contratos e motor computacional de produção;
- `packages/oferbus-db/` — persistência SQLAlchemy/PostgreSQL;
- `packages/oferbus-jobs/` — contrato e implementação inicial da fila assíncrona;
- `packages/oferbus-planning/` — fronteira compartilhada de aplicação para inputs e revisões de planejamento;
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
