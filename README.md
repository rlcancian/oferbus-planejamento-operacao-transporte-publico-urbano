# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano, agora reconstruído como plataforma web multiusuário B2B.

## Estado atual

A arqueologia do sistema legado foi consolidada, o núcleo computacional de referência já possui caracterização executável, o primeiro modelo moderno de persistência PostgreSQL foi formalizado e a arquitetura alvo do OferBus 2026 foi aceita.

A implementação entrou na **Phase A — Platform Skeleton**.

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

## Estrutura

- `apps/web/` — shell da aplicação Next.js;
- `apps/api/` — API FastAPI;
- `apps/worker/` — fronteira para jobs assíncronos;
- `packages/oferbus-core/` — destino do motor computacional de produção;
- `reference-core/` — implementação arqueológica executável e testes de caracterização;
- `docs/` — arqueologia, domínio, computação, persistência, decisões e arquitetura.

## Princípios

- preservar separadamente `legacy-exact`, `normalized` e `modern`;
- PostgreSQL é persistência moderna; arquivos históricos são apenas evidência/migração eventual;
- IA interpreta e orquestra, mas não inventa resultados nem escreve SQL diretamente;
- alterações manuais e ações da IA são comandos auditáveis;
- cenários, execuções, planos e resultados são versionados para reprodutibilidade;
- o Gráfico de Marcha permanece um instrumento de engenharia preciso, não uma visualização decorativa;
- visual moderno e 3D complementam, mas não prejudicam, a precisão operacional.

Consulte `docs/README.md` para o índice documental completo.
