# OferBus — Phase B.5 Web Planning Result Workspace v0.1

**Status:** CONCLUÍDA  
**Data:** 2026-10-02

## Objetivo

Transformar a raiz do OferBus no primeiro workspace operacional real da rematerialização, consumindo exclusivamente resultados persistidos e verificados da B.4.

A B.5 não cria dados de demonstração no frontend e não recalcula métricas. Toda informação exibida é obtida pela API autoritativa a partir da linhagem:

```text
ScenarioRevision
→ ComputationRun
→ PlanRevision
→ PlannedTrip / VehicleBlock
→ ResultSnapshot
→ API
→ Next.js workspace
```

## API de descoberta

A API `0.9.0` adiciona:

```text
GET /results/latest
```

O endpoint respeita `result:read`, é escopado pela organização ativa e retorna a revisão computada persistida mais recente da organização.

A resposta de resultados também passou a incluir contexto operacional:

- projeto;
- cenário;
- revisão do cenário;
- linhas associadas ao snapshot de planejamento;
- código público e nome da linha.

O frontend continua sem acesso direto ao PostgreSQL.

## Workspace web

A landing técnica da Phase A foi substituída, quando existe resultado, por uma superfície de engenharia organizada em quatro áreas principais.

### 1. Contexto e resumo operacional

O cabeçalho apresenta:

- projeto / cenário / revisão;
- linha ou conjunto de linhas;
- revisão do plano;
- semantic layer;
- integridade do resultado;
- estado PostgreSQL/API.

O ribbon de resumo apresenta os indicadores de maior frequência de consulta:

- frota efetiva;
- quantidade de viagens;
- passageiros;
- quilometragem diária;
- ocupação média;
- custo diário.

### 2. Quadro de horários

A tabela operacional mostra, por viagem:

- sequência;
- partida e chegada reais;
- tempos virtuais quando divergirem dos reais;
- sentido;
- tipo da operação;
- indicação de viagem expressa;
- bloco/veículo;
- nível de serviço.

Tempos são formatados a partir dos minutos de serviço. Valores além de 24h mantêm explicitamente o deslocamento `D+n`, evitando ambiguidade de operação noturna.

### 3. Blocos de veículo

Cada bloco apresenta:

- número do veículo/bloco;
- número de viagens;
- primeira partida e última chegada;
- sequência ordenada das viagens.

A visualização permanece deliberadamente simples e precisa. Ela é uma preparação para o Gráfico de Marcha da Phase C, não uma tentativa de antecipar sua edição interativa.

### 4. Indicadores e provenance

Os indicadores detalham operação, demanda e custos. A área de provenance apresenta:

- engine e versão;
- semantic layer;
- input fingerprint;
- output fingerprint;
- notas técnicas do modelo;
- IDs do run, plano e snapshot.

O frontend recebe apenas resultados que já passaram pela reconstrução e verificação de fingerprint da B.4.

## Estado vazio

Se não houver `PlanRevision` persistido, o workspace exibe um estado vazio explícito, sem inventar métricas ou horários.

Se API/identidade estiverem indisponíveis, o estado também é distinto. Isso evita confundir ausência de dados com falha de infraestrutura.

## Desenvolvimento local

Em `development`, o server component pode usar automaticamente a identidade determinística criada pelo seed:

- subject `dev:rafael`;
- organização de desenvolvimento determinística.

Há overrides opcionais:

```text
OFERBUS_WEB_DEV_SUBJECT
OFERBUS_WEB_DEV_ORGANIZATION_ID
```

Essa conveniência não é usada em `production`/`prod`; nesses ambientes nenhuma identidade local é injetada pelo frontend.

## Linguagem visual

A B.5 adota uma linguagem de workstation/control room:

- fundo técnico discreto;
- painéis escuros de alta legibilidade;
- acento verde-água para estado e provenance;
- densidade de informação compatível com software de engenharia;
- números tabulares;
- navegação por âncoras para horários, blocos, indicadores e provenance;
- animações curtas somente para entrada/estado;
- `prefers-reduced-motion` respeitado;
- layout responsivo para desktop, tablet e mobile.

A estética evita aparência de landing page comercial e mantém o foco no trabalho do planejador.

## Quality gate

O CI valida:

- TypeScript strict typecheck;
- Next.js production build;
- runtime dependency audit;
- Python tests/lint/audit;
- PostgreSQL 18 + migrations + seed;
- `core-planning` real;
- persistência B.4;
- `/results/computations/{run_id}`;
- `/results/latest`;
- contexto correto de projeto/cenário/linha.

## Fora do escopo

A B.5 não implementa:

- criação/edição de projetos e cenários pela UI;
- submissão de planejamento pelo navegador;
- seleção histórica de várias revisões;
- comparação entre cenários;
- Gráfico de Marcha interativo;
- edição manual de horários/blocos;
- visualização 3D;
- Copilot contextual dentro do workspace.

Esses itens serão introduzidos incrementalmente depois que a Phase B fechar seu gate de aceitação na B.6.
