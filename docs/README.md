# OferBus — documentação de reconstrução

Este diretório é a fonte canônica dos artefatos produzidos durante a arqueologia e rematerialização do OferBus.

## Documento de entrada

Para uma visão única e atual do que foi recuperado do sistema legado, comece por:

- `archaeology/OferBus_Consolidated_Archaeology_v1.0.md`

Esse documento consolida domínio, pipeline, modelos computacionais, gráfico de marcha, programação por veículo, frota, indicadores, custos, multilinha, tripulação, persistência, defeitos candidatos, maturidade e UNKNOWNs ainda relevantes.

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

## Persistência moderna

- `persistence/OferBus_PostgreSQL_Persistence_Model_v0.1.md`
- `persistence/OferBus_PostgreSQL_Logical_DDL_v0.1.sql`

A persistência moderna é baseada em PostgreSQL. Arquivos nativos históricos são considerados apenas fontes arqueológicas e, quando útil, entradas para migração única.

## Decisões

- `decisions/ADR-0001-modern-persistence-and-legacy-files.md`

## Reference core

O diretório `../reference-core/` contém a implementação de referência usada para converter a semântica recuperada do Visual Basic em contratos computacionais executáveis e testes de caracterização. Ele não representa ainda a arquitetura de produção.

## Próximo gate

Depois da consolidação arqueológica, o próximo gate é definir a **Rematerialization Architecture**: arquitetura funcional/técnica, fronteiras de subsistemas, tecnologias e plano de implementação. Nenhum framework adicional deve ser considerado decidido antes dessa discussão.
