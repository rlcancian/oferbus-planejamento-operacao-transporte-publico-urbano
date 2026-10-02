# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência possui caracterização executável, o modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A implementação está na **Phase A — Platform Skeleton**:

- **A.1 — Platform Skeleton:** concluída;
- **A.2 — Persistence Baseline:** concluída;
- **A.3 — Identity and Tenancy Boundary:** próxima;
- **A.4 — Asynchronous Computation Boundary:** pendente;
- **A.5 — AI and Tool Boundary:** pendente;
- **A.6 — Quality Gate and Local Startup:** pendente.

## Arquitetura aceita

- Next.js 16 + React 19 + TypeScript no frontend;
- FastAPI/Python como backend autoritativo de aplicação;
- OferBus Core Python independente, determinístico e versionado;
- PostgreSQL como fonte de verdade;
- SQLAlchemy + Alembic + psycopg na camada de persistência Python;
- workers Python para computações longas, com tecnologia de fila ainda em avaliação;
- SVG/D3 para engenharia 2D e Three.js/React Three Fiber para visualizações 3D quando agregarem valor;
- OferBus Copilot/Planning Agent como componente nativo, sempre operando por ferramentas e comandos validados;
- monólito modular, não microserviços prematuros.

## Baseline PostgreSQL A.2

A primeira migration física já cria organizações/usuários, municípios/operadores/terminais, linhas/sentidos, projetos, cenários/revisões e `ComputationRun`. As relações tenant-owned críticas usam foreign keys compostas com `organization_id` para impedir referências cruzadas entre organizações no próprio banco.

A API expõe `/health` e `/ready`; a landing Next.js consulta `/ready` e indica visualmente quando PostgreSQL e a migration estão ativos.

## Estrutura

- `apps/web/` — aplicação Next.js;
- `apps/api/` — API FastAPI;
- `apps/worker/` — fronteira para jobs assíncronos;
- `packages/oferbus-db/` — persistência SQLAlchemy/PostgreSQL;
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
