# OferBus — Planejamento da Operação de Transporte Público Urbano

Rematerialização moderna do **OferBus**, sistema histórico de planejamento operacional de linhas de transporte coletivo urbano.

O projeto está atualmente na fase de **arqueologia e reconstrução computacional**. O objetivo imediato é recuperar, especificar e testar o domínio e os algoritmos do sistema legado antes de consolidar a arquitetura da aplicação web.

## Princípios

- arqueologia antes da reimplementação;
- comportamento legado documentado separadamente de correções e modelos modernos;
- algoritmos determinísticos, auditáveis e testáveis;
- rastreabilidade `artefato legado → regra → requisito → implementação → teste`;
- PostgreSQL será a persistência moderna; formatos de arquivo históricos não são requisitos de compatibilidade e só interessam como evidência/migração eventual;
- nenhum mecanismo legado de licenciamento ou dependência Win16 será reutilizado.

## Estrutura atual

- `docs/archaeology/` — relatórios de arqueologia, rastreabilidade e planos de caracterização;
- `docs/domain/` — modelo de domínio reconstruído e matriz de paridade;
- `docs/computational/` — catálogo dos modelos e status da reconstrução matemática;
- `docs/visualization/` — catálogo de gráficos e interações, incluindo o Gráfico de Marcha;
- `docs/legacy/` — inventários e especificações históricas utilizadas como evidência;
- `reference-core/` — núcleo científico de referência usado para caracterizar e testar os algoritmos recuperados. Não representa ainda uma decisão sobre a linguagem da arquitetura final.

## Estado

O núcleo de referência possui testes automatizados para a reconstrução inicial e central dos algoritmos recuperados. A reconstrução prossegue pelo caminho crítico: demanda → TPV/IR → períodos típicos → quadro mínimo de horários → gráfico de marcha/vinculação → programação por veículo → frota.
