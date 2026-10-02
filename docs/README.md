# OferBus — documentação de reconstrução

Este diretório é a fonte canônica dos artefatos produzidos durante a arqueologia e rematerialização do OferBus.

## Estado atual

### Arqueologia

- `archaeology/OferBus_Archaeology_Traceability_Register_v0.1.md`
- `archaeology/OferBus_Characterization_and_Golden_Master_Test_Plan_v0.1.md`

### Domínio

- `domain/OferBus_Feature_Parity_Matrix_v0.1.md`

### Reconstrução computacional

- `computational/OferBus_Computational_Reconstruction_Status_v0.1.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.2.md`
- `computational/OferBus_Computational_Reconstruction_Status_v0.3.md`
- `computational/OferBus_Central_Planning_Engine_Reconstruction_v0.2.md`

### Decisões

- `decisions/ADR-0001-modern-persistence-and-legacy-files.md`

## Artefatos históricos ainda a consolidar no repositório

Os artefatos abaixo já foram produzidos durante a investigação e serão incorporados ao `main` em unidades pequenas de execução:

- `OferBus_Legacy_System_Archaeology_Report_v0.2.md`
- `OferBus_Reconstructed_Domain_Model_v0.1.md`
- `OferBus_Computational_Model_Catalog_v0.1.md`
- `OferBus_Graphics_and_Interactive_Visualization_Catalog_v0.1.md`
- inventários CSV da arqueologia.

O documento sobre formatos legados é mantido apenas como registro arqueológico; compatibilidade continuada com os formatos de arquivo históricos não é requisito da nova aplicação.

## Política de persistência moderna

A persistência moderna será baseada em banco de dados, com PostgreSQL como hipótese principal. Arquivos nativos históricos do OferBus são tratados apenas como fontes de evidência e, quando útil, como entrada para migração única de dados.
