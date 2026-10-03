# OferBus — documentação de reconstrução e rematerialização

Este diretório é a fonte canônica dos artefatos produzidos durante a arqueologia e rematerialização do OferBus.

## Documentos de entrada

Para entender o estado atual, leia nesta ordem:

1. `archaeology/OferBus_Consolidated_Archaeology_v1.0.md` — o que o OferBus histórico é e o que foi recuperado;
2. `architecture/OferBus_Rematerialization_Architecture_v0.1.md` — arquitetura alvo do OferBus 2026;
3. `architecture/OferBus_Phase_A_Platform_Skeleton_Plan_v0.1.md` — plano e estado da Phase A;
4. `architecture/OferBus_Phase_B_Core_Planning_Vertical_Slice_Plan_v0.1.md` — plano e estado da primeira fatia funcional de planejamento;
5. `architecture/OferBus_Phase_B6_Integrated_Acceptance_and_Regression_v0.1.md` — fechamento da Phase B, golden master e aceitação ponta a ponta;
6. `architecture/OferBus_Phase_C_March_Diagram_and_Versioned_Editing_Plan_v0.1.md` — plano da Phase C, Gráfico de Marcha e edição operacional versionada;
7. `domain/OferBus_Graphics_and_Interactive_Visualization_Catalog_v0.1.md` — semântica arqueológica das visualizações, incluindo o Gráfico de Marcha;
8. `architecture/OferBus_Phase_B2_Planning_Input_Persistence_v0.1.md` — persistência de datasets observados e snapshots imutáveis de planejamento;
9. `architecture/OferBus_Phase_B3_Deterministic_Planning_Worker_v0.1.md` — execução assíncrona determinística, fingerprints e provenance;
10. `architecture/OferBus_Phase_B4_Plan_Result_Persistence_v0.1.md` — linhagem imutável de planos, viagens, blocos e resultados;
11. `architecture/OferBus_Phase_B5_Web_Planning_Result_Workspace_v0.1.md` — primeiro workspace operacional web sobre resultados reais;
12. `architecture/OferBus_Identity_and_Tenancy_v0.1.md` — autenticação substituível, tenancy explícita e autorização;
13. `architecture/OferBus_Phase_A4_Async_Computation_Boundary_v0.1.md` — fila, worker, retries, idempotência e progresso;
14. `decisions/ADR-0005-ai-provider-and-tool-boundary.md` — fronteira provider-neutral do Copilot e ferramentas estruturadas;
15. `persistence/OferBus_PostgreSQL_Persistence_Model_v0.1.md` — contrato conceitual/lógico de persistência.

## Estado da materialização

- **Phase A.1–A.6 — Platform Foundation:** concluída e validada localmente;
- **Phase B — Core Planning Vertical Slice:** concluída e validada ponta a ponta;
- **Phase C.1 — March Read Model and Read-only SVG Surface:** concluída;
- **Phase C.2 — Versioned Editing Domain and Persistence Boundary:** próxima;
- **Phase C.3 — Time Editing and Operational Conflict Validation:** pendente;
- **Phase C.4 — Trip and Block/Link Editing:** pendente;
- **Phase C.5 — Dependent Result Recalculation and Comparison:** pendente;
- **Phase C.6 — Undo/Redo, Audit, Acceptance and Density Gate:** pendente.

## Arqueologia

- `archaeology/OferBus_Consolidated_Archaeology_v1.0.md`
- `archaeology/OferBus_Legacy_System_Archaeology_Report_v0.2.md`
- `archaeology/OferBus_Archaeology_Traceability_Register_v0.1.md`
- `archaeology/OferBus_Characterization_and_Golden_Master_Test_Plan_v0.1.md`
- `archaeology/OferBus_Legacy_File_Format_Spec_v0.1.md`

## Domínio e paridade funcional

- `domain/OferBus_Reconstructed_Domain_Model_v0.1.md`
- `domain/OferBus_Feature_Parity_Matrix_v0.1.md`
- `domain/OferBus_Graphics_and_Interactive_Visualization_Catalog_v0.1.md`

## Reconstrução computacional

- `computational/OferBus_Computational_Model_Catalog_v0.1.md`
- `computational/OferBus_Central_Planning_Engine_Reconstruction_v0.2.md`
- `computational/OferBus_Curve_Models_Characterization_v0.1.md`
- `computational/OferBus_Results_Occupancy_and_Costs_Characterization_v0.1.md`
- `computational/OferBus_Results_Occupancy_and_Costs_Characterization_v0.2.md`
- `computational/OferBus_Return_Trips_and_Fine_Adjustment_Characterization_v0.1.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.1.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.2.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.3.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.4.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.5.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.6.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.7.md`

## Arquitetura

- `architecture/OferBus_Rematerialization_Architecture_v0.1.md`
- `architecture/OferBus_Phase_A_Platform_Skeleton_Plan_v0.1.md`
- `architecture/OferBus_Phase_B_Core_Planning_Vertical_Slice_Plan_v0.1.md`
- `architecture/OferBus_Phase_B2_Planning_Input_Persistence_v0.1.md`
- `architecture/OferBus_Phase_B3_Deterministic_Planning_Worker_v0.1.md`
- `architecture/OferBus_Phase_B4_Plan_Result_Persistence_v0.1.md`
- `architecture/OferBus_Phase_B5_Web_Planning_Result_Workspace_v0.1.md`
- `architecture/OferBus_Phase_B6_Integrated_Acceptance_and_Regression_v0.1.md`
- `architecture/OferBus_Phase_C_March_Diagram_and_Versioned_Editing_Plan_v0.1.md`
- `architecture/OferBus_Phase_A2_Persistence_Baseline_v0.1.md`
- `architecture/OferBus_Identity_and_Tenancy_v0.1.md`
- `architecture/OferBus_Phase_A4_Async_Computation_Boundary_v0.1.md`
- `architecture/OferBus_Phase_A6_Quality_Gate_and_Local_Startup_v0.1.md`

## Persistência, execução e interface modernas

- `persistence/OferBus_PostgreSQL_Persistence_Model_v0.1.md`
- `persistence/OferBus_PostgreSQL_Logical_DDL_v0.1.sql`
- `../packages/oferbus-core/` — contratos, validação, fingerprints canônicos, golden master e ponte de referência;
- `../packages/oferbus-db/` — modelos SQLAlchemy para inputs, execução e resultados operacionais;
- `../packages/oferbus-planning/` — fronteira de aplicação para datasets, revisões de cenário e persistência/reconstrução de resultados;
- `../packages/oferbus-jobs/` — fila PostgreSQL, leases/retries, fingerprints de execução e idempotência estrita;
- `../apps/worker/` — handlers `platform-smoke` e `core-planning`, incluindo persistência idempotente do resultado;
- `../apps/api/` — API autoritativa, incluindo resultados e `GET /plans/{plan_revision_id}/march`;
- `../apps/web/` — workspace operacional Next.js com timetable, blocos, indicadores, provenance e Gráfico de Marcha SVG;
- `../packages/oferbus-ai/` — contrato provider-neutral e ferramentas estruturadas do Copilot;
- `../migrations/` — migrations Alembic; a baseline atual termina em `0005_planning_results`;
- `../scripts/integration_smoke.py` — smoke repetível de cálculo/persistência/API/read model da marcha;
- `../scripts/web_acceptance.py` — aceitação semântica do workspace e do Gráfico de Marcha renderizados;
- `../.github/workflows/ci.yml` — quality gates automatizados, incluindo Next.js de produção sobre o resultado real.

PostgreSQL é a fonte de verdade. Arquivos nativos históricos são apenas fontes arqueológicas e, quando útil, entradas para migração única.

## Decisões

- `decisions/ADR-0001-modern-persistence-and-legacy-files.md`
- `decisions/ADR-0002-application-architecture-and-stack.md`
- `decisions/ADR-0003-identity-tenancy-and-authorization.md`
- `decisions/ADR-0004-postgresql-backed-asynchronous-computation.md`
- `decisions/ADR-0005-ai-provider-and-tool-boundary.md`

## Reference core

`../reference-core/` contém a implementação de referência usada para converter a semântica recuperada do Visual Basic em contratos computacionais executáveis e testes de caracterização. Ele permanece separado do `oferbus-core` de produção; na Phase B é acessado apenas por uma ponte explicitamente temporária e rastreável.
