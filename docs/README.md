# OferBus — documentação de reconstrução e rematerialização

Este diretório é a fonte canônica dos artefatos produzidos durante a arqueologia e rematerialização do OferBus.

## Documentos de entrada

Para entender o estado atual, leia nesta ordem:

1. `archaeology/OferBus_Consolidated_Archaeology_v1.0.md` — o que o OferBus histórico é e o que foi recuperado;
2. `architecture/OferBus_Rematerialization_Architecture_v0.1.md` — arquitetura alvo do OferBus 2026;
3. `architecture/OferBus_Phase_A_Platform_Skeleton_Plan_v0.1.md` — plano e estado da Phase A;
4. `architecture/OferBus_Phase_A2_Persistence_Baseline_v0.1.md` — baseline PostgreSQL física;
5. `architecture/OferBus_Identity_and_Tenancy_v0.1.md` — autenticação substituível, tenancy explícita e autorização;
6. `architecture/OferBus_Phase_A4_Async_Computation_Boundary_v0.1.md` — fila, worker, retries, idempotência e progresso;
7. `decisions/ADR-0005-ai-provider-and-tool-boundary.md` — fronteira provider-neutral do Copilot e ferramentas estruturadas;
8. `persistence/OferBus_PostgreSQL_Persistence_Model_v0.1.md` — contrato conceitual/lógico de persistência.

## Estado da materialização

- **Phase A.1 — Platform Skeleton:** concluída;
- **Phase A.2 — Persistence Baseline:** concluída;
- **Phase A.3 — Identity and Tenancy Boundary:** concluída;
- **Phase A.4 — Asynchronous Computation Boundary:** concluída;
- **Phase A.5 — AI and Tool Boundary:** concluída;
- **Phase A.6 — Quality Gate and Local Startup:** próxima.

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
- `architecture/OferBus_Phase_A2_Persistence_Baseline_v0.1.md`
- `architecture/OferBus_Identity_and_Tenancy_v0.1.md`
- `architecture/OferBus_Phase_A4_Async_Computation_Boundary_v0.1.md`

## Persistência e execução moderna

- `persistence/OferBus_PostgreSQL_Persistence_Model_v0.1.md`
- `persistence/OferBus_PostgreSQL_Logical_DDL_v0.1.sql`
- `../packages/oferbus-db/` — modelos SQLAlchemy da baseline física;
- `../packages/oferbus-jobs/` — contrato de fila e implementação PostgreSQL inicial;
- `../packages/oferbus-ai/` — contrato provider-neutral e ferramentas estruturadas do Copilot;
- `../migrations/` — migrations Alembic; a baseline atual termina em `0003_async_computation`.

PostgreSQL é a fonte de verdade. Arquivos nativos históricos são apenas fontes arqueológicas e, quando útil, entradas para migração única.

## Decisões

- `decisions/ADR-0001-modern-persistence-and-legacy-files.md`
- `decisions/ADR-0002-application-architecture-and-stack.md`
- `decisions/ADR-0003-identity-tenancy-and-authorization.md`
- `decisions/ADR-0004-postgresql-backed-asynchronous-computation.md`
- `decisions/ADR-0005-ai-provider-and-tool-boundary.md`

## Reference core

`../reference-core/` contém a implementação de referência usada para converter a semântica recuperada do Visual Basic em contratos computacionais executáveis e testes de caracterização. Ele permanece separado do `oferbus-core` de produção até promoção deliberada dos módulos.
