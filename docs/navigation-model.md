# Modelo de Navegação do ProcDoc RSC

## 1. Objetivo

Este documento define os espaços de trabalho do ProcDoc RSC e a lógica pela
qual o usuário transita entre eles durante a construção de um projeto. Ele
complementa o modelo do domínio e o workflow: enquanto esses documentos
explicam o que existe e como o processo de negócio acontece, o modelo de
navegação organiza os contextos nos quais o usuário realiza esse trabalho.

O modelo não determina aparência ou disposição visual. Seu propósito é
estabelecer:

- quais espaços de trabalho são necessários;
- qual objetivo cada espaço atende;
- quando o usuário precisa acessá-lo;
- quais relações permitem avançar ou retornar no processo;
- como progresso, pendências e contexto permanecem compreensíveis.

A navegação deve apoiar tanto uma sessão contínua de trabalho quanto a retomada
de um projeto após semanas ou meses.

## 2. Princípios Gerais

### Navegação orientada ao projeto

Todo espaço de trabalho existe dentro do contexto de um Projeto RSC. O usuário
deve compreender qual projeto está sendo tratado, qual é seu estado geral e
como a informação consultada contribui para sua preparação.

### Foco na atividade

A Atividade Profissional é o principal eixo de navegação. Documentos, Eventos
Documentais, Períodos de Exercício, enquadramentos e pontuações devem poder ser
compreendidos a partir das atividades que sustentam.

Também devem existir perspectivas próprias para documentos e eventos, pois um
mesmo elemento pode participar de várias atividades. O foco na atividade não
elimina essas relações transversais.

### Navegação coerente com o workflow

A sequência natural acompanha a construção do projeto: lembrar atividades,
reunir documentos, interpretar eventos, consolidar períodos, enquadrar,
calcular, revisar e organizar o dossiê.

Essa sequência orienta, mas não restringe. O processo é iterativo e deve
permitir retornos quando novas informações alterarem conclusões anteriores.

### Rastreabilidade

O usuário deve conseguir percorrer as relações nos dois sentidos. A partir de
uma atividade, deve alcançar suas fontes; a partir de um documento, deve
identificar os eventos e atividades relacionados; a partir de uma pontuação,
deve retornar ao enquadramento, ao período e às evidências que a justificam.

### Baixa carga cognitiva

Cada espaço deve reunir decisões de uma mesma natureza. O usuário não deve
precisar reconstruir mentalmente o contexto ao mudar de etapa. Identidade da
atividade, estado, pendências e relações relevantes devem permanecer
compreensíveis ao longo da navegação.

### Progresso visível

O projeto deve comunicar:

- o que já foi registrado;
- o que já foi comprovado e revisado;
- o que ainda precisa de trabalho;
- quais inconsistências impedem o avanço;
- quais atividades estão prontas;
- qual é o estado geral do projeto.

Progresso não deve ser confundido com simples passagem por um espaço. Ele
decorre de decisões e revisões efetivamente concluídas.

### Retomada contextual

Ao retomar um projeto, o usuário deve reconhecer o último contexto relevante,
as pendências abertas e as próximas ações possíveis. A navegação não deve
depender da memória de quem realizou o trabalho anteriormente.

### Independência tecnológica

Os espaços e suas relações representam necessidades do processo de RSC. Sua
validade não depende de uma solução técnica específica.

## 3. Estrutura Geral

O ProcDoc RSC é organizado nos seguintes espaços conceituais:

```text
Projeto RSC
    ↓
Visão Geral
    ↓
Atividades
    ↔ Documentos
    ↔ Eventos Documentais
    ↔ Períodos
    ↓
Normativa
    ↓
Pontuação
    ↓
Revisão
    ↓
Dossiê
```

A representação mostra uma direção predominante, mas não uma sequência rígida.
Atividades, Documentos, Eventos Documentais e Períodos formam um núcleo de
análise com circulação frequente entre seus espaços. Normativa e Pontuação
dependem dessa análise, enquanto Revisão e Dossiê avaliam e organizam o
resultado do conjunto.

### Visão Geral

Oferece orientação sobre estado, progresso, pendências e próximas ações do
projeto.

### Atividades

Organiza aquilo que o servidor realizou e acompanha a evolução de cada
atividade ao longo do processo.

### Documentos

Reúne as fontes documentais, seu grau de análise e suas relações com
atividades.

### Eventos Documentais

Organiza as informações relevantes extraídas das fontes e sua situação de
revisão.

### Períodos

Permite acompanhar a reconstrução temporal das atividades a partir dos
eventos.

### Normativa

Concentra o entendimento da normativa aplicável e os enquadramentos
argumentados das atividades.

### Pontuação

Apresenta os cálculos, suas bases, limites e situação de conferência.

### Revisão

Reúne verificações documentais, cronológicas, normativas e de pontuação.

### Dossiê

Organiza o material revisado para apresentação e conferência.

## 4. Área Inicial do Projeto

Ao abrir um projeto, o usuário deve encontrar orientação suficiente para
compreender sua situação sem percorrer todos os espaços.

A área inicial deve comunicar conceitualmente:

- identificação e finalidade do projeto;
- estado geral, como novo, em construção ou em revisão;
- quantidade e situação das atividades;
- documentos reunidos e ainda não analisados;
- atividades aguardando documentos;
- eventos pendentes de revisão;
- períodos incompletos ou incertos;
- enquadramentos ainda não realizados;
- cálculos que precisam ser revistos;
- inconsistências relevantes;
- progresso da revisão;
- situação do dossiê;
- últimas mudanças relevantes;
- próximos trabalhos recomendados.

As informações devem conduzir aos espaços correspondentes sem impor uma ordem
única. Se a principal pendência for uma atividade sem comprovação, o percurso
natural leva à atividade e às suas fontes. Se houver cálculos desatualizados, o
percurso leva à pontuação e às causas da atualização.

A área inicial não substitui os demais espaços. Ela sintetiza o projeto e
ajuda o usuário a decidir onde continuar.

## 5. Espaço de Trabalho das Atividades

O espaço de Atividades é o centro da trajetória profissional. Ele é utilizado
desde o registro da lembrança inicial até a preparação final do dossiê.

Nesse espaço, o usuário deve conseguir compreender:

- quais atividades foram lembradas;
- qual descrição e período foram inicialmente alegados;
- qual é o estado de cada atividade;
- quais possuem fontes relacionadas;
- quais já possuem eventos identificados;
- quais períodos estão em análise ou consolidados;
- quais foram enquadradas e pontuadas;
- quais pendências impedem sua conclusão;
- quais atividades podem ser duplicadas ou relacionadas.

A criação de uma atividade ocorre mesmo antes de existirem fontes localizadas.
À medida que o trabalho avança, sua apresentação deve refletir a diferença
entre lembrança, interpretação, comprovação, enquadramento e revisão.

O usuário deve poder partir de uma atividade para consultar:

- documentos relacionados;
- eventos que a sustentam;
- períodos construídos;
- enquadramento adotado;
- pontuação resultante;
- inconsistências e pendências;
- participação da atividade no dossiê e na linha do tempo.

Atividades incompletas não devem desaparecer nem ser apresentadas como
inválidas. Seu estado deve indicar claramente o trabalho ainda necessário.

## 6. Espaço de Trabalho dos Documentos

O espaço de Documentos organiza as fontes reunidas para o projeto. Ele é
utilizado durante a busca, inclusão, classificação, análise e revisão
documental.

O usuário deve conseguir distinguir:

- documentos ainda não analisados;
- documentos potencialmente relevantes;
- documentos relacionados a uma ou mais atividades;
- documentos dos quais já surgiram eventos;
- documentos com problemas de legibilidade ou identificação;
- documentos considerados irrelevantes para determinada atividade;
- documentos que exigem nova conferência.

A classificação deve ajudar a compreender a natureza e o contexto da fonte sem
transformá-la automaticamente em prova de uma atividade.

Um documento pode ser reutilizado por várias atividades. A navegação deve
permitir visualizar todas essas relações sem duplicar a fonte. Também deve ser
possível partir do documento para seus Eventos Documentais e, por meio deles,
para as atividades sustentadas.

Documentos ainda sem atividade relacionada devem permanecer localizáveis. Eles
podem estar aguardando análise ou representar material que não será utilizado.

## 7. Espaço de Trabalho dos Eventos Documentais

O espaço de Eventos Documentais apresenta as informações relevantes
identificadas nas fontes. Ele é utilizado para interpretar, revisar e organizar
as unidades que contribuirão para a reconstrução da trajetória.

Cada evento deve ser compreendido junto de:

- documento de origem;
- localização da informação, quando aplicável;
- natureza da ocorrência;
- pessoas e atividades relacionadas;
- datas ou vigências identificadas;
- situação de interpretação e revisão;
- incertezas ou divergências;
- participação na formação de períodos.

O usuário deve conseguir analisar eventos por atividade, por documento, por
período e por situação de revisão. Essa multiplicidade evita que a informação
fique isolada de seu contexto.

Eventos sugeridos e ainda não confirmados devem ser claramente distinguíveis
dos eventos revisados. Uma sugestão futura de apoio automatizado somente poderá
avançar no workflow após conferência humana.

A navegação a partir de um evento deve permitir retornar à fonte, consultar a
atividade sustentada e compreender seu papel temporal.

## 8. Espaço de Trabalho dos Períodos

O espaço de Períodos organiza a reconstrução cronológica das atividades. Ele é
utilizado quando já existem eventos suficientes para analisar início,
continuidade, interrupção e encerramento.

O usuário deve conseguir observar:

- período inicialmente lembrado;
- eventos utilizados na reconstrução;
- data inicial e sua fonte;
- eventos de continuidade;
- alterações que não interrompem a atuação do servidor;
- data final e sua fonte;
- lacunas documentais;
- inferências realizadas;
- sobreposições com outros períodos;
- estado de consolidação e revisão.

A navegação deve permitir seguir a cadeia temporal de eventos sem reduzir o
período a uma simples lista cronológica de documentos.

Quando houver continuidade provável, mas não explicitamente declarada, a
incerteza deve permanecer visível. Quando existirem períodos descontínuos ou
sobrepostos, o usuário deve poder analisá-los no contexto das atividades
envolvidas.

Do período, deve ser possível alcançar a atividade correspondente, os eventos
que formam seus limites e os enquadramentos que utilizam sua duração.

## 9. Espaço de Trabalho Normativo

O espaço Normativo é utilizado quando uma atividade possui compreensão e
comprovação suficientes para ser comparada aos critérios aplicáveis.

Ele deve permitir ao usuário compreender:

- qual versão da normativa rege o projeto;
- quais itens podem ser pertinentes às atividades;
- quais requisitos e limites precisam ser observados;
- quais atividades aguardam enquadramento;
- quais enquadramentos estão propostos, confirmados ou pendentes;
- qual justificativa sustenta cada associação;
- quais fontes e períodos apoiam a justificativa;
- onde pode existir conflito ou dupla contagem.

A navegação deve partir tanto da atividade para os itens possíveis quanto do
Item Normativo para as atividades relacionadas. Essa visão cruzada ajuda a
identificar concentrações, omissões e enquadramentos concorrentes.

Uma associação ainda incerta deve permanecer diferenciada de uma associação
revisada. Alterações em períodos ou evidências devem indicar que o
enquadramento correspondente necessita de nova conferência.

## 10. Espaço de Trabalho da Pontuação

O espaço de Pontuação acompanha os resultados derivados dos enquadramentos. Ele
é utilizado após existir informação consolidada suficiente para realizar os
cálculos e volta a ser consultado sempre que suas bases forem alteradas.

O usuário deve conseguir compreender:

- qual atividade e enquadramento originam cada resultado;
- qual quantidade foi apurada;
- qual regra e valor foram aplicados;
- quais limites incidiram;
- qual era o resultado antes dos limites;
- qual é o resultado considerado;
- quais cálculos aguardam revisão;
- quais resultados ficaram desatualizados;
- onde pode existir dupla contagem;
- como as pontuações se distribuem por item ou categoria.

A navegação não deve apresentar apenas totais. Todo resultado deve permitir o
retorno ao enquadramento, período, eventos e documentos que o fundamentam.

O progresso desse espaço depende da qualidade das etapas anteriores. Um cálculo
concluído pode voltar a ficar pendente quando uma atividade ou período é
revisto.

## 11. Espaço de Trabalho da Revisão

O espaço de Revisão reúne as verificações necessárias antes de considerar o
projeto pronto. Ele não substitui as revisões realizadas em cada espaço; oferece
uma perspectiva integrada das pendências.

As inconsistências devem ser organizadas por natureza:

- documentais, como fonte ilegível ou sem rastreabilidade suficiente;
- cronológicas, como lacunas, contradições e sobreposições;
- de atividade, como ausência de comprovação ou possível duplicidade;
- normativas, como requisito não demonstrado ou enquadramento concorrente;
- de pontuação, como cálculo desatualizado, limite incorreto ou dupla contagem;
- de dossiê, como material incompleto ou sem sequência compreensível.

Cada pendência deve indicar:

- o que precisa ser verificado;
- por que isso é relevante;
- quais elementos estão envolvidos;
- qual espaço oferece o contexto para tratá-la;
- se ela impede a prontidão do projeto;
- qual é sua situação atual.

Ao selecionar uma inconsistência, o usuário deve chegar ao contexto de origem e
depois retornar à revisão. Pendências resolvidas devem conservar registro
suficiente para explicar a decisão tomada.

## 12. Espaço de Trabalho do Dossiê

O espaço do Dossiê prepara o material revisado para apresentação e conferência.
Ele é utilizado quando atividades, períodos, enquadramentos e pontuações
atingem maturidade suficiente.

O usuário deve conseguir acompanhar:

- quais atividades foram incluídas;
- qual ordem favorece a compreensão;
- quais períodos alegados e comprovados serão apresentados;
- quais documentos sustentam cada atividade;
- quais justificativas normativas acompanham o material;
- quais memórias de cálculo estão disponíveis;
- quais pendências ainda impedem a finalização;
- como a linha do tempo contribui para a leitura do conjunto.

A navegação pelo dossiê deve manter o acesso às fontes e às decisões que
produziram cada conclusão. Preparar o material não significa copiar ou alterar
os documentos originais.

Esse espaço deve permitir avaliar a completude do conjunto antes de marcar o
projeto como pronto para envio. O material poderá subsidiar externamente a
redação do memorial, que não integra o ProcDoc RSC.

## 13. Navegação Entre Espaços

A navegação principal segue o progresso do workflow, mas permite circulação
por relações contextuais.

Um percurso típico é:

```text
Visão Geral
    ↓
Atividade lembrada
    ↓
Documentos relacionados
    ↓
Eventos identificados
    ↓
Período consolidado
    ↓
Enquadramento normativo
    ↓
Pontuação
    ↓
Revisão
    ↓
Dossiê
```

Há também percursos transversais:

```text
Documento → Eventos → Atividades relacionadas

Atividade → Períodos → Eventos → Documento de origem

Pontuação → Enquadramento → Atividade → Período → Evidências

Pendência de revisão → Contexto de origem → Revisão
```

O usuário deve sempre reconhecer:

- o projeto atual;
- o espaço de trabalho atual;
- o elemento em análise;
- sua situação no workflow;
- as pendências relacionadas;
- os caminhos naturais de continuidade e retorno.

Ao mudar de espaço, o contexto selecionado deve ser preservado quando fizer
sentido. Por exemplo, partir de uma atividade para seus documentos não deve
obrigar o usuário a procurar novamente a mesma atividade ao retornar.

A Visão Geral funciona como ponto de orientação, mas não como passagem
obrigatória. Relações diretas reduzem deslocamentos e preservam o raciocínio do
usuário.

## 14. Situações Especiais

### Projeto incompleto

A Visão Geral deve mostrar o estado alcançado e as principais pendências. Todos
os espaços continuam acessíveis conforme o conteúdo existente, sem sugerir que
o projeto está pronto.

### Documentos pendentes

Documentos ainda não localizados devem aparecer como pendências das atividades
que necessitam deles. Documentos já reunidos, mas não analisados, devem ser
distinguíveis dos ainda ausentes.

### Atividade sem documentos

A atividade permanece no espaço de Atividades com seu caráter lembrado ou
alegado. O usuário deve conseguir registrar pistas para busca e compreender que
ela ainda não possui comprovação.

### Documento sem atividade

O documento permanece disponível para análise. Pode ser posteriormente
relacionado, considerado irrelevante ou mantido como fonte ainda não
classificada.

### Eventos pendentes de confirmação

Eventos interpretados, mas não revisados, devem permanecer identificados. Sua
utilização em períodos e enquadramentos deve conservar essa ressalva.

### Períodos incompletos

Períodos sem início ou encerramento comprovado devem aparecer com suas lacunas.
O usuário deve poder navegar até os eventos existentes e às pendências
documentais correspondentes.

### Pendências normativas

Atividades sem enquadramento, com requisitos incompletos ou com associações
concorrentes devem ser localizáveis tanto no espaço Normativo quanto na
Revisão.

### Revisão incompleta

O projeto permanece em construção ou revisão. Pendências impeditivas devem ser
visíveis na Visão Geral e no Dossiê, evitando uma indicação prematura de
prontidão.

### Retomada após longo intervalo

A entrada no projeto deve priorizar contexto: estado geral, mudanças recentes,
último foco relevante, decisões já confirmadas e pendências abertas. O usuário
deve conseguir continuar sem depender de lembranças externas ao próprio
projeto.

## 15. Evolução Futura

Novas capacidades poderão ser incorporadas aos espaços existentes desde que
preservem a lógica principal da navegação:

```text
atividade
  → fontes
  → interpretação
  → consolidação
  → enquadramento
  → pontuação
  → revisão
  → dossiê
```

A Inteligência Artificial poderá futuramente sugerir classificações, eventos,
relações, lacunas, continuidades ou possíveis enquadramentos. Essas sugestões
devem aparecer no espaço em que a decisão correspondente já ocorre, sem criar
um percurso paralelo desconectado do workflow.

O usuário continuará distinguindo sugestões de informações revisadas. O
ProcDoc permanecerá responsável por preservar o estado do projeto, a
rastreabilidade, as regras, as pendências e as decisões confirmadas.
