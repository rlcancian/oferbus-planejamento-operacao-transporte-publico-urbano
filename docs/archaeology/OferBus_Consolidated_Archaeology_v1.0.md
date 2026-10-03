# OferBus — Consolidated Archaeology v1.0

**Status:** visão consolidada da arqueologia e reconstrução já realizadas.  
**Data:** 2026-10-02.  
**Escopo:** explicar o que o OferBus é, o que foi recuperado, o que já foi reconstruído executavelmente, o que deve ser preservado e o que continua incerto. Este documento **não define ainda arquitetura web, frameworks, stack de aplicação ou deploy**.

## 1. Resposta executiva: o que é o OferBus

O OferBus é um sistema de **planejamento operacional de linhas de transporte coletivo urbano**. Sua função não é apenas montar uma tabela de horários. O sistema recebe dados observados de operação e demanda, reconstrói curvas temporais, aplica modelos de previsão e ajuste, determina a oferta necessária segundo nível de serviço e restrições, gera viagens, constrói a circulação operacional dos veículos, calcula a frota e produz indicadores técnicos e econômicos.

O produto central do OferBus é, portanto, um **plano operacional completo**, contendo simultaneamente:

- demanda e suas curvas temporais;
- tempos de viagem;
- índice de renovação;
- especificações de planejamento;
- quadro de horários;
- viagens normais e deslocamentos expressos sem passageiros;
- horários reais e virtuais;
- vínculos entre viagens;
- gráfico de marcha;
- programação por veículo;
- frota efetiva e de reserva;
- ocupação e nível de serviço;
- quilometragem, produtividade e custos;
- comparação entre alternativas;
- intervenções manuais do planejador;
- em versões tardias, planejamento multilinha e escala de tripulação.

O procedimento `Make_Urban_Line_Project`, no módulo legado `MPROCEDI.BAS`, é comentado no próprio código como **“CORAÇÃO DO OFERBUS”** e confirma esse pipeline integrado.

## 2. O que diferencia o OferBus de um simples gerador de horários

A arqueologia mostra cinco características distintivas.

### 2.1 O horário é consequência da demanda

O sistema não parte simplesmente de intervalos arbitrários. Ele reconstrói demanda minuto a minuto e usa capacidade, nível de serviço, índice de renovação e intervalo máximo para determinar partidas.

### 2.2 O horário precisa ser operacionalmente realizável

Depois de criar partidas, o sistema precisa verificar se os veículos conseguem efetivamente encadear as viagens. Surgem daí:

- retornos;
- viagens expressas/deadhead sem passageiros;
- estocagem em terminal;
- garagem;
- tempos reais e virtuais;
- vínculos de entrada e saída;
- blocos de veículos.

### 2.3 A frota emerge da programação

A frota efetiva não é apenas um parâmetro informado. Ela resulta das cadeias de viagens que podem ser executadas por um mesmo veículo. Quando uma cadeia nova é necessária, cresce a frota lógica.

### 2.4 O gráfico de marcha é um editor operacional

O gráfico de marcha não é uma figura estática. Ele funciona como superfície de planejamento. O usuário cria, remove e desloca viagens, altera vínculos e observa o efeito das decisões sobre circulação, frota e resultados.

### 2.5 O sistema combina cálculo automático com decisão humana

O OferBus preserva intervenções do projetista. O código distingue viagens geradas automaticamente, importadas ou criadas manualmente, bem como alterações manuais de horário e vínculos. Um recálculo não deve apagar silenciosamente decisões humanas.

## 3. Tecnologia e arquitetura histórica

A implementação principal analisada é uma aplicação desktop Win16 em Visual Basic clássico, com forte evidência de Visual Basic 3. O projeto ativo contém dezenas de forms e módulos `.BAS`, usa controles `.VBX`, APIs Win16 e bibliotecas auxiliares históricas.

O pacote inclui ainda um helper Delphi 7 usado para compatibilidade de diálogos/identificação/licenciamento.

Componentes históricos como VBX, EVERLOCK, Crystal Reports legado, WinHelp, DLLs proprietárias e integração antiga com Windows não possuem valor arquitetural para a rematerialização. O patrimônio a preservar está no domínio, nos modelos computacionais e nas interações de planejamento.

## 4. Modelo de domínio recuperado

### 4.1 Linha

A linha contém identificação, operador/empresa, cidade, tipo de operação, terminais, extensões por sentido, parâmetros econômicos, possibilidade de estocagem e parâmetros de planejamento.

Foram recuperados sete tipos históricos de operação:

1. Circular;
2. Radial-Circular;
3. Diametral-Circular;
4. Periférica-Circular;
5. Radial;
6. Diametral;
7. Periférica.

Esses tipos afetam como sentidos e retornos são tratados.

### 4.2 Sentido

O sistema histórico trabalha principalmente com até dois sentidos, mas isso decorre dos arrays e da representação legada. A semântica moderna recuperada é simplesmente uma direção operacional pertencente a uma linha.

### 4.3 Terminal, estocagem e garagem

Terminais não são apenas pontos de origem/destino. A existência ou não de área de estocagem afeta diretamente a construção da programação. Garagem e estocagem são tipos distintos de origem/destino de blocos e vínculos.

### 4.4 Veículo e modelo de veículo

Um modelo de veículo registra número de assentos, área livre para passageiros em pé e quantidade disponível. A capacidade admissível é calculada em função do nível de serviço.

### 4.5 Levantamento operacional

O levantamento contém viagens observadas com:

- horário;
- passageiros transportados;
- passageiros no trecho crítico;
- tempo de viagem.

Esses dados alimentam demanda, tempo de percurso e índice de renovação.

### 4.6 Demanda mensal

Há série histórica mensal utilizada para previsão. O limite legado de 60 meses é artefato de implementação, não requisito do domínio.

### 4.7 Especificação de projeto

A especificação governa o cálculo e contém, entre outros:

- nível de serviço;
- intervalo máximo;
- método de demanda;
- uso ou não de previsão;
- criação de retornos expressos;
- graus de ajuste de demanda, tempo de viagem e índice de renovação;
- configuração de períodos típicos;
- nível de vale;
- ajuste histórico de partidas para minutos terminados em 0/5;
- descrição do projeto.

### 4.8 Viagem planejada

A entidade historicamente chamada `TpObjViagem` é central. Possui:

- linha;
- sentido;
- saída real;
- saída virtual;
- chegada real;
- chegada virtual;
- tipo/proveniência;
- vínculo de entrada;
- vínculo de saída;
- veículo;
- motorista;
- cobrador;
- nível de serviço.

### 4.9 Proveniência da viagem

O campo histórico `Tipo` é um bit field. Foram recuperadas semânticas para:

- viagem expressa;
- viagem criada;
- horário alterado;
- criada pelo projetista versus importada;
- vínculo de entrada alterado manualmente;
- vínculo de saída alterado manualmente.

Na rematerialização isso não deve continuar como inteiro opaco: são conceitos distintos do domínio.

### 4.10 Vínculos

O campo histórico `Vinculos` compacta dois vínculos independentes — entrada e saída. Cada extremidade pode representar:

- nenhum vínculo;
- garagem;
- área de estocagem;
- continuidade com outra viagem.

O modelo moderno deve tratá-los como relações estruturadas.

## 5. Dados e transformação temporal

OferBus trabalha fortemente com curvas em resolução de um minuto.

O pipeline recuperado é:

`observações por viagem → passageiros/minuto → curva diária → suavização → correção de massa → modelo de demanda → oferta necessária`.

Essa resolução temporal não é detalhe de UI. Ela influencia o quadro de horários, tempos virtuais e ocupação.

## 6. Modelos de demanda

### 6.1 Modelo de Demanda Variável

A demanda diária é representada por uma curva contínua ajustada ao longo do dia.

### 6.2 MPTDC — Modelo de Períodos Típicos de Demanda Constante

O modelo transforma a curva em patamares de demanda aproximadamente constante. As fronteiras surgem de cruzamentos com faixas horizontais e períodos muito curtos são eliminados.

Foi encontrada divergência importante entre manual e código:

- Manual 2005: suavização intermediária com grau 3 e número de faixas igual ao grau escolhido;
- Código 2008c: força grau 2 e usa o dobro do parâmetro para quantidade de faixas.

Consequência: não existe uma única “verdade histórica”. Devem coexistir variantes versionadas.

## 7. Tempo de viagem

O OferBus reconstrói uma curva temporal de tempo de viagem a partir das observações e a suaviza usando infraestrutura semelhante à da demanda.

Também existe tempo de viagem específico para viagens expressas/deadhead.

A reconstrução executável já caracteriza um erro histórico relacionado à sentinela `-2`: o código testa `2` em uma condição. Isso pode tanto deixar um final ausente sem correção quanto modificar uma observação legítima igual a 2 minutos. O comportamento histórico e a variante corrigida já estão separados.

## 8. IR — Índice de Renovação

O Índice de Renovação transforma passageiros transportados em estimativa de passageiros no trecho crítico. Há dois modos:

- IR constante/médio;
- IR variável ao longo do dia.

Quando o IR é calculado como curva, o sistema também mantém sua média, utilizada em alguns indicadores agregados.

A curva variável é limitada inferiormente a 1 e pode ser suavizada.

## 9. Previsão de demanda

Foram recuperados modelos históricos de previsão:

- parabólico;
- logarítmico;
- exponencial.

O sistema calcula erro de ajuste e pode selecionar automaticamente o modelo histórico com melhor desempenho segundo sua métrica. Há ainda tratamento para séries curtas e cálculo de fator de previsão para aplicar ao dia típico.

Esses modelos fazem parte do patrimônio computacional; modelos modernos futuros deverão ser adicionais, não substituições silenciosas.

## 10. Capacidade e nível de serviço

O OferBus deriva capacidade admissível a partir de:

- número de assentos;
- área livre para passageiros em pé;
- nível de serviço.

A fórmula histórica corresponde a incrementos de densidade em pé associados aos níveis A–F.

Há forte candidato a defeito no código: em determinado cálculo, o modelo do veículo solicitado parece ser carregado, mas a capacidade pode continuar sendo calculada com o veículo padrão. O reference core mantém variante histórica e variante corrigida separadas.

## 11. Horários reais e horários virtuais

Essa é uma das ideias mais importantes recuperadas.

O horário real é a partida/chegada operacional apresentada ao usuário. O horário virtual desloca a viagem para incorporar tempos associados a embarque/desembarque e é usado para decidir se duas viagens podem ser fisicamente encadeadas.

Portanto, `SaidaVirtual` e `ChegadaVirtual` não são metadados de visualização. São parte da mecânica de compatibilidade operacional.

## 12. Quadro mínimo de horários

O procedimento histórico de 2007 percorre o período operacional minuto a minuto e acumula demanda. Uma partida pode ser disparada por uma combinação de:

- capacidade atingida;
- intervalo máximo;
- limites temporais;
- necessidade de retorno;
- estocagem.

Depois surgem regras adicionais de fechamento/regularização da programação.

O manual apresenta a intenção como maximização de intervalos sob restrições. O código é uma heurística construtiva mais rica. A equivalência formal entre as duas descrições não foi demonstrada.

O reference core já executa os ramos principais caracterizados.

## 13. Retornos e viagens expressas

Uma **viagem expressa**, no sentido do OferBus recuperado, é um deslocamento operacional de veículo **sem passageiros**, necessário para reposicionar o veículo para outro terminal/posição operacional.

Ela deve:

- ocupar tempo e veículo;
- participar da circulação;
- aumentar quilometragem/custos quando aplicável;
- reduzir a taxa média de ocupação global ao aparecer como movimento com ocupação zero;
- não consumir demanda de passageiros.

A arqueologia recuperou duas famílias principais de criação de retornos (`Cria_1` e `Cria_2`). Diversos ramos já estão executáveis no reference core. Fallbacks raros e inconsistentes de `Cria_2` permanecem explicitamente não normalizados.

## 14. Vinculação de viagens

A etapa de vinculação conecta uma viagem a outra quando há compatibilidade temporal e operacional.

A sequência reconstruída inclui:

1. vínculos diretos entre viagens;
2. vínculos por estocagem;
3. preenchimento dos extremos remanescentes por garagem.

Vínculos manuais podem ser protegidos contra recálculo automático.

## 15. Programação por veículo

Uma vez construído o grafo de vínculos, o sistema atribui um identificador lógico de veículo a cada cadeia. O mesmo veículo continua executando viagens compatíveis ao longo do dia.

A entidade conceitual moderna que emerge é o **Vehicle Block** — bloco operacional de veículo.

Essa abstração não existia explicitamente como entidade limpa no legado, mas está claramente implícita no algoritmo.

## 16. Frota

### 16.1 Frota efetiva

É a quantidade de blocos lógicos necessários para executar o plano.

### 16.2 Frota reserva

É calculada aplicando percentual configurado sobre a frota efetiva, com arredondamento histórico caracterizado.

A frota é, portanto, resultado do planejamento e não apenas dado de entrada.

## 17. Nível de serviço por viagem

O sistema estima a carga no trecho crítico para cada viagem e a converte em nível de serviço segundo o veículo associado.

Foi recuperado também um detalhe de perda de informação histórica: sobrecargas além de F podem produzir rótulos como `F1`, `F2`, etc., mas outra rotina reduz o resultado ao primeiro caractere e armazena todos como nível 5/F.

## 18. Ocupação

A arqueologia e a intervenção do autor fecharam a semântica correta:

- viagem normal transporta a demanda acumulada desde a última viagem normal;
- viagem expressa/deadhead transporta zero passageiros;
- a taxa média de ocupação **global** deve incluir as viagens expressas no denominador como movimentos com ocupação zero;
- uma métrica complementar, **taxa média de ocupação operacional**, pode excluir os deslocamentos expressos e medir somente viagens com passageiros.

O código legado de uma das rotinas atribui indevidamente demanda à viagem expressa antes de calcular a média. Isso agora é tratado como comportamento `legacy-exact`, enquanto a semântica do domínio fica em `normalized`.

## 19. Indicadores recuperados

Entre os resultados calculados estão:

- passageiros totais;
- número de viagens;
- frota efetiva;
- frota reserva;
- quilometragem diária total;
- percurso médio por veículo;
- passageiros médios por viagem;
- passageiros médios no trecho crítico;
- taxa média de ocupação;
- índice de passageiros por quilômetro;
- viagens médias por veículo;
- tempo médio de viagem;
- velocidade média programada;
- custo diário total;
- custo médio por veículo;
- custo por viagem;
- custo por passageiro equivalente;
- pior ocupação;
- pior densidade no trecho crítico.

## 20. Custos

Foram recuperados dois modos principais:

1. custo por quilômetro;
2. custo fixo por veículo + custo variável por quilômetro.

Também foi recuperada conversão histórica de custo diário para mensal conforme tipo de dia.

Há candidato a defeito importante na quilometragem projetada: o cálculo histórico usa `número total de viagens × extensão média`. Para sentidos com extensões diferentes e quantidades assimétricas de viagens, isso diverge da soma fisicamente adequada `Σ viagens_do_sentido × extensão_do_sentido`.

As duas variantes estão separadas em `legacy-exact` e `normalized`.

## 21. Gráfico de marcha

O gráfico de marcha é provavelmente a principal interface técnica do produto.

Ele representa:

- tempo;
- viagens;
- sentidos;
- terminais;
- horários reais/virtuais;
- vínculos;
- estocagem;
- garagem;
- blocos/veículos;
- viagens normais e expressas.

Operações históricas confirmadas incluem:

- selecionar e inspecionar viagem;
- criar viagem;
- apagar viagem;
- mover viagem;
- mover conjuntos de viagens;
- alterar duração/tipo;
- alterar vínculos;
- zoom;
- alternar visão real/virtual;
- undo;
- redo.

Uma nova versão que apenas desenhasse um gráfico sem edição **não teria paridade funcional com o OferBus**.

## 22. Programação por veículo

Há também representação tabular/gráfica por veículo, mostrando sequências, intervalos, estocagem, movimentos e uso do veículo.

O gráfico de marcha e a programação por veículo são visões diferentes do mesmo plano operacional e deverão permanecer sincronizadas conceitualmente.

## 23. Comparação de alternativas

OferBus trabalha com alternativas de projeto e comparação de resultados. Isso é parte essencial do processo de engenharia: alterar especificações, recalcular e comparar frota, custo, ocupação, oferta e outras métricas.

A persistência moderna já foi desenhada para transformar essa ideia histórica em cenários e revisões imutáveis.

## 24. Otimizador de projeto

O “otimizador” legado não é um solver matemático global no sentido moderno.

Ele enumera combinações discretas de parâmetros como:

- previsão;
- ajuste 0/5;
- ajustes de IR, tempo e demanda;
- método de demanda;
- intervalo máximo;
- retorno normal/expresso;
- nível de serviço;
- nível de vale.

Para cada combinação ele executa o planejamento e filtra resultados segundo restrições de custo, frota, ocupação, viagens e outros limites.

Sua classificação correta é uma **busca enumerativa de alternativas de projeto**. Deve ser preservada como algoritmo legado, sem ser confundida com otimização moderna futura.

## 25. Planejamento multilinha

Há evidência real de evolução para projetos com várias linhas:

- projeto multilinha;
- cadastro de linhas participantes;
- deslocamentos entre terminais;
- possibilidade de compartilhar/remanejar recursos;
- integração com programação/escala.

O suporte está parcialmente desenvolvido e não deve ser descrito como totalmente acabado. Entretanto, ele demonstra que o domínio moderno não deve impor `projeto = uma linha`.

## 26. Escala de tripulação

O módulo de tripulação é grande e substancial, embora historicamente evolutivo.

Conceitos recuperados:

- funcionários;
- motorista/cobrador;
- duplas;
- jornadas;
- custos normal/noturno/extra;
- intervalos;
- horas extras;
- deslocamentos;
- trocas de linha/veículo;
- faixas proibidas;
- períodos de uso;
- programação por funcionário;
- validação de restrições;
- pelo menos dois algoritmos automáticos.

O segundo algoritmo executa tentativas e escolhe alternativas segundo uma heurística gulosa, com memória opcional. Não há evidência de solução global ótima.

Esse subsistema deve ser preservado como patrimônio funcional, mas sua reconstrução ainda não está suficientemente fechada para congelar o esquema detalhado definitivo.

## 27. Relatórios e visualizações

O legado contém relatórios e gráficos para:

- identificação da linha;
- frota;
- levantamento;
- demanda mensal;
- demanda diária;
- previsão;
- tempo de viagem;
- IR;
- lotação;
- oferta levantada/projetada;
- demanda × oferta;
- horários;
- gráfico de marcha;
- programação por veículo;
- indicadores/custos;
- comparação levantamento × projeto;
- multilinha;
- cadastro e escala de tripulação.

Alguns relatórios ficaram desatualizados durante a evolução histórica. A rematerialização deve preservar o conteúdo técnico útil, não copiar layouts de impressão antigos.

## 28. Persistência histórica

O legado usa manifestos `.OFB`/`.PML` e diversos arquivos auxiliares, vários binários e versionados ao longo do tempo.

Decisão já tomada:

- esses formatos não fazem parte da arquitetura futura;
- podem servir para migração única de dados históricos;
- não haverá requisito de continuar salvando projetos nesses formatos;
- compatibilidade binária não deve contaminar o domínio moderno.

## 29. Persistência moderna já formalizada

PostgreSQL foi definido como persistência moderna.

A linhagem central proposta é:

`Organization → PlanningProject → Scenario → ScenarioRevision → ComputationRun → PlanRevision → ResultSnapshot`.

Isso permite:

- entradas imutáveis;
- cenários reproduzíveis;
- versão explícita dos algoritmos;
- comparação `legacy-exact` × `normalized` × futuros modelos modernos;
- edição manual sem sobrescrever o plano automático;
- auditoria completa da origem de cada resultado.

O esquema físico de produção ainda não está congelado; existe apenas contrato conceitual e DDL lógico de referência.

## 30. Camadas semânticas adotadas

### `legacy-exact`

Reproduz exatamente o comportamento histórico conhecido, inclusive peculiaridades e defeitos quando isso é necessário para caracterização.

### `normalized`

Representa a semântica correta do OferBus recuperado, corrigindo bugs de implementação comprovados ou representações artificiais do legado.

### `modern`

Reservada para modelos futuros melhores, cientificamente/operacionalmente atualizados.

Essa separação evita dois erros: destruir o patrimônio histórico ao “corrigir” tudo e, no sentido oposto, perpetuar defeitos antigos por falsa fidelidade.

## 31. Estado do reference core

Foi criado um núcleo computacional de referência independente de UI e banco.

Ele não é ainda a arquitetura de produção. Serve para transformar o código VB em contratos executáveis.

Até o checkpoint v0.7 existem **52 testes automatizados passando** cobrindo, entre outros:

- demanda e suavização;
- conservação de massa;
- previsão;
- capacidade;
- tempos virtuais;
- TPV;
- IR;
- MPTDC;
- quadro mínimo;
- atributos das viagens;
- retornos `Cria_1`;
- ramos caracterizados de `Cria_2`;
- vínculos;
- estocagem e garagem;
- blocos/frota;
- nível de serviço;
- ajuste fino;
- verificação de expressos órfãos;
- intervalo inferior a quatro minutos;
- ocupação;
- indicadores;
- custos;
- fixture end-to-end em memória.

Isso significa que parte considerável do conhecimento que antes existia apenas no Visual Basic já foi convertida em comportamento executável e testável.

## 32. Defeitos candidatos e divergências relevantes

Os principais itens atualmente registrados incluem:

- capacidade aparentemente usando o veículo padrão em determinado cálculo;
- índice incorreto em replay de demanda do quadro mínimo;
- confusão `2`/`-2` na curva de tempo de viagem;
- comportamento semelhante no IR;
- quilometragem projetada baseada em extensão média em vez de ponderação por sentido;
- código inalcançável após `Cria_2` por zerar variável imediatamente antes de testá-la;
- uso do vínculo de `i` duas vezes no ajuste fino em vez de `i` e `j`;
- inconsistência de provenance bit em um retorno normal;
- estado compartilhado suspeito no MPTDC radial;
- atribuição de demanda a viagem expressa na taxa média de ocupação legado;
- possibilidade de pular remoções consecutivas em `Verifica_Ida_Garagem`;
- fallbacks de `Cria_2` sem estocagem com expressões inconsistentes/arriscadas.

A política é sempre a mesma: registrar, caracterizar, reproduzir quando necessário e corrigir apenas em variante explícita.

## 33. O que constitui patrimônio do OferBus e deve ser preservado

### Patrimônio computacional

- reconstrução de demanda;
- suavização e períodos típicos;
- previsão histórica;
- TPV;
- IR;
- capacidade e nível de serviço;
- quadro mínimo;
- tempos reais/virtuais;
- retornos;
- vínculos;
- programação por veículo;
- frota;
- indicadores e custos.

### Patrimônio operacional

- gráfico de marcha editável;
- programação por veículo;
- intervenção manual com proveniência;
- comparação de alternativas;
- relação explícita entre demanda, oferta, frota e custo;
- possibilidade de operar em contexto multilinha;
- escala de tripulação como subsistema futuro de paridade.

### Patrimônio conceitual

- horário como parte de um plano operacional, não como objetivo isolado;
- frota como consequência das cadeias;
- distinção real/virtual do tempo;
- expressos como movimentos vazios necessários à operação;
- coexistência de cálculo automático e decisão do planejador.

## 34. O que não precisa ser preservado

Não fazem parte do patrimônio funcional:

- Visual Basic/Win16;
- `.VBX`;
- WinHelp;
- EVERLOCK;
- DLLs de impressão;
- Crystal Reports legado;
- compactação auxiliar histórica;
- limites fixos de arrays;
- estruturas binárias dos arquivos;
- convenções de caminhos DOS/Windows;
- associação de extensões de arquivos;
- estética visual da aplicação de 1990/2000.

## 35. Maturidade por subsistema

| Subsistema | Estado arqueológico atual |
|---|---|
| Domínio principal | alto / consolidado |
| Demanda | alto |
| Previsão histórica | alto |
| TPV | alto, com variante histórica/corrigida |
| IR | alto estrutural |
| MPTDC | alto estrutural, com divergência manual × código |
| Quadro mínimo | alto estrutural; alguns caminhos raros ainda pendentes |
| Viagens/tempos reais-virtuais | alto |
| Vinculação | alto |
| Programação por veículo | alto |
| Frota | alto |
| Nível de serviço | alto |
| Ocupação | alto após esclarecimento semântico |
| Indicadores/custos | alto estrutural |
| Gráfico de marcha | alto semanticamente; interação web ainda futura |
| Comparação de alternativas | alta conceitualmente |
| Persistência moderna | contrato PostgreSQL v0.1 definido |
| Otimizador legado | médio/parcial |
| Multilinha | médio/parcial |
| Tripulação | médio/alto arqueológico, reconstrução incompleta |
| Paridade numérica com executável histórico | ainda não fechada |

## 36. UNKNOWNs que ainda importam

A arqueologia central está suficientemente madura, mas permanecem pendências reais:

1. identidade numérica completa frente ao executável histórico;
2. alguns fallbacks raros de geração/retorno;
3. comportamento completo de variantes históricas de arquivos/dados;
4. alguns relatórios e suas fórmulas exatas;
5. completude final de multilinha;
6. completude final dos dois algoritmos de escala de tripulação;
7. significado operacional de algumas rotinas históricas incompletas/TODO;
8. confirmação empírica, por datasets reais, de alguns defeitos candidatos.

Essas lacunas não impedem compreender o núcleo do produto, mas impedem declarar “100% de paridade histórica” neste momento.

## 37. Conclusão arqueológica

O principal risco inicial da rematerialização era construir um novo sistema com o nome OferBus mas perder o conhecimento embutido no programa original. Esse risco foi substancialmente reduzido.

Hoje é possível afirmar com segurança que o OferBus é um sistema integrado de engenharia operacional que transforma dados de demanda e operação em um plano de oferta executável, editável e economicamente analisável.

O núcleo conceitual e computacional está suficientemente recuperado para iniciar uma discussão arquitetural moderna **sem depender da tecnologia antiga**.

Entretanto, a arquitetura não deve ser escolhida apenas por conveniência de stack. Ela deve ser avaliada contra os requisitos arqueologicamente demonstrados:

- motor computacional determinístico e versionável;
- cenários e revisões reproduzíveis;
- gráfico de marcha altamente interativo;
- edição manual auditável;
- recomputação de dependências;
- programação por blocos de veículos;
- comparação de alternativas;
- visualizações científicas/operacionais;
- futura extensão multilinha e tripulação;
- execução de modelos `legacy-exact`, `normalized` e `modern` lado a lado;
- persistência PostgreSQL com proveniência.

A próxima decisão deve, portanto, ser uma **Rematerialization Architecture**, derivada desse patrimônio e não de uma preferência prévia por framework.
