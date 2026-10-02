# OferBus — Graphics and Interactive Visualization Catalog v0.1

**Status:** catálogo arqueológico inicial das visualizações e interações.  
**Objetivo:** preservar a semântica técnica das representações gráficas antes de qualquer redesign web.

## Princípio

As visualizações do OferBus não são decoração. Elas sustentam decisões de planejamento e, em alguns casos, funcionam como editores operacionais. A rematerialização deve preservar significado, unidades, relações e efeitos de edição, ainda que abandone completamente a estética Win16.

## Catálogo resumido

| ID | Visualização | Propósito | Interatividade histórica | Paridade |
|---|---|---|---|---|
| VIS-DMD-001 | Demanda diária | inspecionar distribuição temporal da demanda | consulta/ajuste indireto | obrigatória |
| VIS-DMD-002 | Demanda observada × ajustada | avaliar suavização | comparação visual | obrigatória |
| VIS-DMD-003 | MPTDC | visualizar patamares típicos | parametrização indireta | obrigatória |
| VIS-MON-001 | Demanda mensal/série histórica | analisar evolução temporal | seleção de período/modelo | obrigatória |
| VIS-FC-001 | Previsão | comparar histórico e curvas previstas | escolha de modelo | obrigatória |
| VIS-TT-001 | Tempo de viagem | analisar TPV por horário | comparação observado/ajustado | obrigatória |
| VIS-IR-001 | Índice de renovação | analisar IR diário | comparação/ajuste | obrigatória |
| VIS-OFR-001 | Oferta planejada | visualizar oferta por período | consulta | obrigatória |
| VIS-DO-001 | Demanda × oferta | avaliar adequação da oferta | comparação | obrigatória |
| VIS-LOAD-001 | Lotação / NS | identificar saturação e serviço | inspeção | obrigatória |
| VIS-MARCH-001 | Gráfico de marcha | visualizar e editar a programação | extensa | central/obrigatória |
| VIS-VEH-001 | Programação por veículo | visualizar blocos/cadeias | edição/inspeção | obrigatória |
| VIS-CREW-001 | Escala da tripulação | visualizar programação por funcionário | edição/inspeção | futura obrigatória para paridade |
| VIS-CMP-001 | Comparação de alternativas | comparar cenários/resultados | seleção de cenários | obrigatória |

## VIS-MARCH-001 — Gráfico de Marcha

### Papel

**CONFIRMADO NO CÓDIGO E NA DOCUMENTAÇÃO:** é um componente central do OferBus e um editor operacional, não apenas um gráfico estático.

### Semântica recuperada

Representa:

- eixo temporal;
- sentidos da linha;
- terminais;
- viagens;
- horários reais e virtuais;
- viagens normais e expressas;
- relações/vínculos entre viagens;
- veículos/cadeias operacionais;
- origem/destino em garagem;
- áreas de estocagem;
- retornos;
- consequências da ausência/presença de estocagem.

### Operações históricas relevantes

Foram recuperadas operações de:

- selecionar/inspecionar viagem;
- alterar horário;
- criar viagem;
- remover viagem;
- alterar tipo/expresso;
- mudar vínculos;
- reorganizar cadeias;
- alterar associação operacional;
- refletir mudanças em programação/frota;
- navegar/visualizar regiões distintas do gráfico.

Os bits de `TpObjViagem.Tipo` registram parte da proveniência dessas alterações, incluindo edição manual de horário e vínculos.

### Critério de paridade web

A versão web só satisfaz paridade quando o planejador consegue, no navegador:

1. identificar univocamente cada viagem;
2. distinguir sentidos e tipos de viagem;
3. visualizar relações operacionais;
4. editar partidas/viagens/vínculos;
5. receber validação imediata de conflitos/restrições;
6. observar efeitos dependentes em blocos, frota e indicadores;
7. desfazer/refazer operações críticas;
8. preservar autoria/proveniência da intervenção manual;
9. impedir que um recálculo sobrescreva silenciosamente uma decisão manual.

### Tecnologia web

**Ainda não decidida.** SVG é candidato natural para semântica vetorial e interação; Canvas pode ser útil para grandes volumes; WebGL só deve ser usado se benchmarks demonstrarem necessidade. D3 pode auxiliar escalas/eixos, mas não deve impor o modelo de interação. A escolha depende de testes com densidade real de viagens.

## VIS-VEH-001 — Programação por veículo

### Propósito

Mostrar a sequência diária de viagens atribuída a cada veículo lógico, evidenciando blocos operacionais, tempos ociosos, retornos e transições entre terminais/estocagem/garagem.

### Relação com o domínio

`viagens → vínculos → vehicle block → veículo lógico → frota efetiva`

A visualização não deve tratar o veículo como simples cor ou rótulo: ela representa a consequência de uma cadeia operacional.

### Paridade

- identificar todas as viagens de um bloco;
- detectar sobreposição/incompatibilidade;
- permitir inspeção cruzada com o gráfico de marcha;
- refletir alterações manuais;
- destacar criação/eliminação de veículo lógico;
- apresentar períodos ociosos e deslocamentos relevantes.

## VIS-CREW-001 — Escala da tripulação

O legado contém interface gráfica substancial para escala. Ela mostra programação por funcionário, períodos de trabalho, relação com veículos e violações/restrições. Como o módulo é historicamente evolutivo, a paridade deverá ser definida após fechamento da reconstrução computacional de tripulação.

A versão moderna deverá separar:

- restrições históricas recuperadas;
- políticas configuráveis;
- legislação/regulação vigente;
- violações duras;
- advertências;
- decisões manuais justificadas.

## Demanda diária

A curva diária deriva dos dados levantados por viagem e da reconstrução minuto a minuto. Há interesse técnico em mostrar simultaneamente:

- curva original;
- curva ajustada;
- períodos típicos, quando usados;
- limites/picos relevantes;
- escala temporal e unidade explícita.

A versão web deve permitir inspeção pontual, comparação de modelos e identificação do algoritmo/versão que produziu a curva.

## Demanda mensal e previsão

A visualização histórica sustenta a análise da série mensal e a escolha/avaliação de previsões. Na versão moderna deve ser possível sobrepor:

- observações;
- curva parabólica;
- curva logarítmica;
- curva exponencial;
- modelo escolhido;
- horizonte previsto;
- métricas de ajuste.

Novos modelos futuros devem aparecer como séries adicionais versionadas, sem esconder os métodos legados.

## Tempo de viagem

Deve representar observações e curva ajustada ao longo do dia, por sentido. Pontos fora do domínio ou dados ausentes precisam ser explicitamente distinguidos de zero.

## Índice de renovação

Deve permitir verificar IR médio e/ou variável, mostrar dados observados/reconstruídos e identificar períodos onde a curva é inferida ou completada.

## Demanda × oferta / lotação / nível de serviço

Essas visualizações sustentam a decisão de planejamento. A versão moderna deve relacionar temporalmente:

- demanda acumulada/instantânea;
- capacidade admissível;
- oferta realizada;
- partidas;
- lotação estimada;
- nível de serviço.

Quando uma alteração manual de horário cria violação, a visualização deve deixar a relação causal observável.

## Comparação de cenários

A comparação moderna deve operar sobre cenários imutavelmente identificados. Não deve combinar gráficos de resultados produzidos por parâmetros/modelos diferentes sem mostrar as diferenças de proveniência.

Dimensões recuperadas/esperadas:

- número de viagens;
- frota efetiva/reserva;
- quilometragem;
- ocupação;
- nível de serviço;
- IPK;
- custos;
- demanda/oferta;
- distribuição temporal;
- programação por veículo.

## Requisitos transversais para a versão web

- escalas e unidades explícitas;
- tooltips/inspeção sem ocultar dados;
- zoom/pan quando necessário;
- seleção cruzada entre tabela e gráfico;
- edição apenas onde houver semântica bem definida;
- teclado/atalhos para planejadores avançados;
- acessibilidade de cores e não dependência exclusiva de cor;
- exportação vetorial/PDF quando aplicável;
- snapshot de cenário e versão do algoritmo;
- desempenho medido com datasets reais;
- testes de interação para operações críticas.

## Não objetivos

A modernização visual não deve transformar o OferBus em roteador GIS ou dashboard genérico. Mapas podem ser acrescentados futuramente, mas não substituem as visualizações temporais e operacionais que constituem o núcleo histórico.

## Status

| Área | Estado |
|---|---|
| Inventário das famílias de gráficos | PASS inicial |
| Semântica do gráfico de marcha | PASS estrutural avançado |
| Operações de edição da marcha | PASS estrutural |
| Programação por veículo | PASS estrutural |
| Demanda/TPV/IR/previsão | PASS estrutural |
| Escala da tripulação | PARTIAL avançado |
| Critérios visuais pixel-a-pixel | NÃO APLICÁVEL |
| Tecnologia gráfica web | NÃO DECIDIDA |
