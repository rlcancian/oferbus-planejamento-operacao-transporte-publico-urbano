# OferBus — Characterization and Golden-Master Test Plan v0.1

**Fase:** fechamento da arqueologia / preparação da reconstrução computacional.  
**Objetivo:** definir como provar equivalência antes de portar algoritmos para qualquer stack moderna.

## 1. Situação observada

Uma busca recursiva no pacote recebido não encontrou arquivos nativos de projeto/dados com extensões `.OFB`, `.IDF`, `.CFR`, `.LEV`, `.DDM`, `.PRJ`, `.PRV`, `.NUM`, `.DCL`, `.RST`, `.PML`, `.LIN`, `.DES`, `.JOR`, `.CAD`, `.TRI` ou `.OTM` fora do código/documentação.

Portanto:

- há **especificação estática e documentação suficientes para reconstrução**;
- não há, no pacote atual, um par `entrada histórica nativa + saída histórica conhecida` adequado a golden master end-to-end;
- fixtures sintéticas podem provar coerência da especificação reconstruída, mas **não substituem golden masters históricos**.

## 2. Taxonomia de testes

### 2.1 Characterization test

Captura o comportamento de uma implementação/versão específica, inclusive peculiaridades. É o instrumento correto para decidir se um defeito candidato fazia parte do comportamento observado.

### 2.2 Golden-master test

Compara uma entrada histórica preservada com resultado histórico conhecido ou com execução confiável da versão histórica em ambiente isolado. É a evidência principal de paridade.

### 2.3 Specification test

Verifica uma equação/regra reconstruída de forma independente do código VB. Detecta traduções erradas, mas não decide automaticamente divergências código×manual.

### 2.4 Property-based test

Valida invariantes amplos, por exemplo conservação de passageiros ou ausência de sobreposição em blocos.

## 3. Hierarquia de confiança

```text
inspeção visual do código
    < specification test independente
    < characterization test do legado
    < golden master entrada+saída histórica
    < golden master + implementação independente + invariantes
```

Nenhuma função crítica deve ser marcada como `PARITY PASS` apenas por tradução linha a linha.

## 4. Fixtures sintéticas mínimas

| Fixture | Propósito | Dados mínimos | Evidência esperada |
|---|---|---|---|
| FX-DMD-001 | passageiros/minuto | partidas 06:00, 06:10, 06:20 com volumes simples | taxas manualmente calculáveis |
| FX-DMD-002 | partidas coincidentes | duas partidas no mesmo minuto | ausência de divisão por zero + volume preservado |
| FX-DMD-003 | média móvel | curva curta não constante | pontos de 10 min + bordas verificáveis |
| FX-DMD-004 | correção de massa | curva cuja suavização altera soma | soma final = total alvo dentro da regra legado |
| FX-MPTDC-001 | divergência grau/faixas | curva triangular longa | diferença mensurável entre manual e 2008c |
| FX-TT-001 | TPV interpolado | 3 observações com tempos 30/40/20 | interpolação e bordas |
| FX-IR-001 | PTC ausente | mistura de valores definidos/ausentes | completamento pelo IR adjacente/médio |
| FX-SENT-001 | sentinela IR | último ponto forçado a `-2` | distinguir comportamento `=2` versus `=-2` |
| FX-SENT-002 | sentinela TPV | idem | idem |
| FX-FC-001 | parábola perfeita | 3+ médias anuais sobre parábola exata | erro ~0 e coeficientes esperados |
| FX-FC-002 | exponencial perfeita | série exponencial | seleção exponencial |
| FX-FC-003 | log perfeita | série logarítmica | seleção logarítmica |
| FX-CAP-001 | dois modelos de veículo | modelos com assentos/área diferentes | expor uso indevido de `gVeiculoPadrao` |
| FX-TIME-001 | saída/chegada virtual | lotação, embarque, desembarque e TPV simples | tempos calculáveis manualmente |
| FX-SCH-001 | demanda constante | um sentido, estocagem disponível | headways regulares |
| FX-SCH-002 | pico abrupto | um sentido, demanda variável | partidas adicionais no pico |
| FX-SCH-003 | intervalo máximo | demanda baixa | partida por `IntervaloMax` |
| FX-SCH-004 | sem estocagem | dois sentidos, horários assimétricos | retorno automático |
| FX-SCH-005 | replay retorno | curva fortemente variável | discriminar índice `cont` vs `i` |
| FX-LNK-001 | encode/decode vínculos | todos os 16 pares possíveis | round-trip completo |
| FX-TYPE-001 | bit field `Tipo` | combinações conhecidas | provenance/flags corretos |
| FX-FLT-001 | duas cadeias incompatíveis | 4–6 viagens | frota efetiva = 2 |
| FX-FLT-002 | cadeia contínua | várias viagens compatíveis | um único bloco |
| FX-MET-001 | sentidos assimétricos | extensões e NV distintos | expor `NV×L_médio` versus soma por sentido |
| FX-OPT-001 | espaço discreto pequeno | 2×2×2 combinações | enumeração exatamente reproduzível |
| FX-CREW-001 | conflito temporal | 2 períodos sobrepostos | código de restrição de conflito |
| FX-CREW-002 | terminal incompatível | sequência impossível | diagnóstico de terminal |
| FX-CREW-003 | pequeno problema completo | 2 veículos, 2 funcionários | caracterizar Alg1/Alg2 |

## 5. Testes por modelo crítico

### 5.1 Demanda

Propriedades:

- nenhum passageiro deve desaparecer na reconstrução por intervalos;
- `Corrige_Curva_Ajustada` deve preservar o total segundo sua própria convenção histórica;
- alterar grau de ajuste deve alterar suavidade, não o domínio temporal;
- pontos fora da faixa operacional não devem contaminar o cálculo.

### 5.2 MPTDC — teste de divergência obrigatório

Executar pelo menos três oráculos para a mesma curva:

1. **Manual-2005:** MDV grau 3; `n = grau` faixas;
2. **Code-2008c:** MDV grau 2; `n = 2 × AjustePeriodo`;
3. **candidate-modern:** somente depois, método atual proposto.

A saída deve ser versionada, nunca mesclada. Se um projeto histórico conhecido reproduzir um deles, associar essa semântica à versão correspondente.

## 6. Teste do Quadro de Horários Mínimos

Para cada fixture, registrar:

- curva de demanda usada;
- curva de IR;
- TPV;
- nível de serviço;
- lotação por nível;
- intervalo máximo;
- estocagem;
- primeira/última viagem observada;
- viagens geradas com tipo, real/virtual e sentido;
- retornos criados;
- vínculos após etapa correspondente.

Critérios:

1. demanda acumulada respeita o gatilho histórico;
2. `IntervaloMax` é respeitado segundo a implementação;
3. retornos são criados somente nas condições históricas;
4. limite/âncoras inicial e final são reproduzidos;
5. pós-processamento das últimas viagens é reproduzido;
6. “Ajeitadinha” é testada separadamente on/off;
7. nenhuma correção de defeito candidato entra no legacy core sem versão explícita.

## 7. Teste do Gráfico de Marcha como editor

Cada ação deve ser testada como comando de domínio:

```text
estado inicial
→ comando
→ estado esperado
→ dependências recalculadas
→ flags de provenance/override
→ restrições
→ undo
→ estado inicial equivalente
→ redo
→ estado esperado equivalente
```

Ações mínimas: criar, excluir, mover, deslocar conjunto, alterar TPV, trocar tipo, trocar vínculo, associar veículo.

## 8. Teste de programação/frota

Propriedades:

- toda viagem planejada obrigatória deve pertencer a exatamente um bloco quando a programação está completa;
- duas viagens incompatíveis temporalmente não podem ocupar o mesmo bloco;
- vínculos manuais fixados devem ser respeitados ou produzir violação explícita;
- frota efetiva deve ser derivável do número de blocos/veículos lógicos;
- frota reserva deve ser calculada separadamente.

## 9. Teste de tripulação

Antes de reproduzir o algoritmo automático, testar o `constraint engine` isoladamente. Cada código de erro de `Verifica_Restricoes_Escala` deve ter um fixture que produza somente aquela violação quando possível.

Em seguida comparar Algoritmo 1 e Algoritmo 2 em problemas pequenos onde uma busca exaustiva independente possa calcular a melhor solução possível. Isso permitirá classificar qualidade da heurística sem confundir “produz uma escala” com “produz ótimo”.

## 10. Golden masters históricos desejados

Prioridade de recuperação:

1. um projeto de linha simples de um terminal;
2. um projeto radial de dois terminais com retorno automático;
3. um caso com MPTDC;
4. um caso com IR variável;
5. um caso com previsão;
6. um projeto personalizado manualmente;
7. um projeto com otimizador;
8. um `.PML` multilinha;
9. um caso de escala de tripulação.

Para cada caso, preservar o conjunto inteiro de arquivos associados e, se disponível, PDF/relatório/captura correspondente.

## 11. Execução segura do legado — somente se futuramente necessária

A ausência de golden masters pode justificar executar a versão histórica **apenas em laboratório isolado**, nunca no host operacional. Requisitos mínimos:

- VM descartável/offline;
- snapshot antes/depois;
- sem credenciais/arquivos pessoais;
- sem rede ou com rede bloqueada;
- hashes de todos os binários;
- dependências obtidas de fonte confiável ou de mídia original;
- monitoramento de filesystem/processos;
- nenhum mecanismo antigo de licença contornado de forma não autorizada;
- exportar apenas entradas/saídas de teste.

A execução não é necessária para a arqueologia estática e não foi feita até aqui.

## 12. Gate para iniciar reimplementação do computational core

Pode-se iniciar a reconstrução isolada quando:

- [x] domínio central recuperado;
- [x] catálogo de modelos criado;
- [x] formatos lógicos mapeados;
- [x] divergências código×manual registradas;
- [x] defeitos candidatos registrados;
- [x] fixtures sintéticas especificadas;
- [ ] pelo menos um golden master histórico recuperado **ou** decisão explícita de iniciar com characterization/specification tests enquanto se busca material histórico;
- [ ] convenção de versionamento dos engines aprovada;
- [ ] tolerâncias numéricas por modelo definidas.

**Estado atual:** pronto para começar uma implementação de referência dos algoritmos em isolamento, mas ainda não para afirmar paridade histórica.
