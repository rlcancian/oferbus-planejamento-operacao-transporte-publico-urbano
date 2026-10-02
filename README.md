# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência possui caracterização executável, o modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A implementação está na **Phase A — Platform Skeleton**:

- **A.1 — Platform Skeleton:** concluída;
- **A.2 — Persistence Baseline:** concluída;
- **A.3 — Identity and Tenancy Boundary:** concluída;
- **A.4 — Asynchronous Computation Boundary:** concluída;
- **A.5 — AI and Tool Boundary:** concluída;
- **A.6 — Quality Gate and Local Startup:** próxima.

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

## Fundação multiusuário e Copilot

A baseline física já inclui organizações/usuários, memberships, municípios/operadores/terminais, linhas/sentidos, projetos, cenários/revisões, `ComputationRun`, auditoria e metadados de execução assíncrona. As relações tenant-owned críticas usam foreign keys compostas com `organization_id` para impedir referências cruzadas entre organizações no próprio banco.

A autenticação possui fronteira substituível; o desenvolvimento usa um adaptador local explicitamente proibido em produção. A aplicação resolve uma organização ativa e aplica RBAC (`owner`, `admin`, `planner`, `viewer`).

A fronteira de IA já existe em `packages/oferbus-ai`. Nenhum LLM tem acesso direto a SQL. O provider ainda está deliberadamente `unconfigured`; ferramentas disponíveis são allow-listed, herdam as permissões do usuário e ações de cálculo/mutação exigem confirmação na baseline atual.

A API expõe `/health`, `/ready`, `/identity/me`, `/computations` e `/ai`. A landing Next.js consulta `/ready` e indica visualmente quando PostgreSQL e migrations estão ativos.

## Estrutura

- `apps/web/` — aplicação Next.js;
- `apps/api/` — API FastAPI;
- `apps/worker/` — worker Python para computações longas;
- `packages/oferbus-ai/` — contratos de provider LLM e ferramentas estruturadas do Copilot;
- `packages/oferbus-db/` — persistência SQLAlchemy/PostgreSQL;
- `packages/oferbus-jobs/` — contrato e implementação inicial da fila assíncrona;
- `packages/oferbus-core/` — destino do motor computacional de produção;
- `reference-core/` — implementação arqueológica executável e testes de caracterização;
- `migrations/` — migrations Alembic;
- `infra/dev/` — infraestrutura local opcional;
- `docs/` — arqueologia, domínio, computação, persistência, decisões e arquitetura.

## Princípios

- preservar separadamente `legacy-exact`, `normalized` e `modern`;
- PostgreSQL é persistência moderna; arquivos históricos são apenas evidência/migração eventual;
- IA interpreta e orquestra, mas não inventa resultados nem escreve SQL diretamente;
- alterações manuais e ações da IA são comandos auditáveis;
- cenários, execuções, planos e resultados são versionados para reprodutibilidade;
- o Gráfico de Marcha permanece um instrumento de engenharia preciso;
- visual moderno e 3D complementam, mas não prejudicam, a precisão operacional.

Consulte `docs/README.md` para o índice documental completo.
