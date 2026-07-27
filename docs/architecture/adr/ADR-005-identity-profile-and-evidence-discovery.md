# ADR-005 — Identity Profile & Evidence Discovery

## Status

Proposed

## Contexto

O ProcDocOrganizer reconstrói trajetórias funcionais a partir de evidências
documentais. O pipeline definido no
[Blueprint do Pipeline de Reconstrução Funcional](../functional-reconstruction-pipeline.md)
começa em `Evidence`, mas pressupõe que exista um conjunto inicial de
evidências relacionado à pessoa cuja trajetória se deseja reconstruir.

Antes do pipeline principal, portanto, é necessário definir quem é a pessoa de
interesse e localizar, entre os documentos disponíveis, evidências que possam
estar relacionadas a ela. Essa etapa antecedente não reconstrói fatos. Sua
finalidade é formar, de maneira auditável, o conjunto candidato que alimentará
o pipeline.

Este ADR deve ser interpretado conforme os princípios gerais da
[Visão do Domínio](../domain-vision.md).

## 1. Problema

O sistema precisa determinar de qual pessoa deve reconstruir a trajetória
funcional e localizar as evidências potencialmente relacionadas a essa pessoa.
Essa determinação não pode depender apenas de uma busca exata por nome.

Um documento pode conter dezenas de servidores e registrar fatos diferentes
para cada um. Outros documentos podem mencionar uma pessoa apenas por SIAPE,
CPF ou matrícula institucional. Nomes podem aparecer abreviados, grafados de
formas distintas ou sob nomes anteriormente utilizados. Uma mesma ocorrência
documental também pode conter múltiplos identificadores, enquanto ocorrências
diferentes podem fornecer partes complementares da identificação.

Essas variações criam dois riscos opostos:

- excluir evidências relevantes porque usam uma forma de identificação ainda
  desconhecida;
- incluir evidências de outra pessoa porque compartilham nome ou atributo
  insuficientemente distintivo.

O problema deve ser tratado antes do pipeline principal porque o pipeline
reconstrói fatos a partir das evidências que recebe; ele não é responsável por
procurar indiscriminadamente no acervo nem por definir a pessoa que motivou a
reconstrução. Misturar descoberta e reconstrução faria critérios de busca
interferirem em decisões de identidade funcional, atividade e continuidade,
reduzindo a auditabilidade de todas essas etapas.

O conjunto encontrado nesta fase é candidato. Sua seleção não confirma que
todas as evidências pertencem à mesma identidade funcional e não demonstra a
existência de qualquer exercício.

## 2. Decisão Arquitetural

São formalizados dois conceitos independentes:

- **Identity Profile:** representação do conhecimento disponível sobre a
  pessoa de interesse, usada exclusivamente para orientar a descoberta;
- **Evidence Discovery:** processo que utiliza o `Identity Profile` para
  localizar, extrair e classificar evidências potencialmente relacionadas.

Ambos pertencem à etapa anterior ao pipeline de reconstrução funcional. O
perfil expressa o que é conhecido ou informado para procurar a pessoa; a
descoberta produz as evidências candidatas que serão entregues ao pipeline.

O `Identity Profile` não é um fato funcional e `Evidence Discovery` não é
resolução de identidade. A descoberta avalia a confiança da associação entre
uma ocorrência documental e o perfil usado na busca. A resolução posterior
decidirá, com responsabilidade própria, se evidências normalizadas se referem à
mesma identidade funcional.

As entradas, critérios consultados, fontes pesquisadas, associações produzidas
e confirmações humanas devem permanecer rastreáveis. A ausência de resultado
também não demonstra ausência de trajetória; significa apenas que a descoberta
não localizou evidências segundo o perfil, as fontes e os critérios utilizados.

## 3. Identity Profile

O `Identity Profile` representa o conhecimento conhecido sobre uma pessoa no
contexto da descoberta de evidências. Seu propósito é reunir sinais que possam
ser utilizados para formular pesquisas, reconhecer menções candidatas e
distinguir resultados potencialmente homônimos.

Ele não representa a trajetória funcional, não representa fatos reconstruídos
e não confirma que cargos, instituições ou períodos tenham integrado a
trajetória da pessoa. Seus atributos são pistas de descoberta e devem preservar
a origem, a condição e a confiabilidade com que foram informados ou
descobertos.

Possíveis atributos incluem:

- nome principal;
- nomes alternativos;
- nomes abreviados conhecidos;
- nomes anteriormente utilizados;
- SIAPE;
- CPF;
- matrícula institucional;
- instituições conhecidas;
- cargos conhecidos;
- períodos conhecidos;
- origem de cada atributo;
- condição de confirmação ou incerteza de cada atributo;
- identificadores futuros.

Essa lista é extensível. Novos identificadores ou atributos de contexto podem
ser incorporados sem transformar o perfil em uma representação da carreira.
Dados sensíveis, como CPF, continuam sujeitos às políticas de acesso, proteção
e finalidade aplicáveis, sem que este ADR defina tais políticas.

Instituições, cargos e períodos conhecidos funcionam como contexto auxiliar.
Eles não autorizam a exclusão automática de evidências fora desse contexto nem
podem ser convertidos em fatos históricos apenas por constarem do perfil.

## 4. Evidence Discovery

`Evidence Discovery` recebe um `Identity Profile` e procura ocorrências
documentais potencialmente relacionadas à pessoa de interesse.

Suas responsabilidades são:

- receber o perfil e preservar a origem dos atributos utilizados;
- localizar documentos candidatos nas fontes disponíveis;
- identificar, em cada documento candidato, todas as ocorrências relevantes
  para a associação pesquisada;
- extrair todas as evidências relacionadas encontradas, mantendo referência
  precisa ao documento e ao trecho de origem;
- avaliar a confiança de cada associação entre a evidência e o perfil;
- preservar resultados concorrentes, insuficientes ou ambíguos;
- registrar fontes consultadas e critérios de descoberta aplicados;
- produzir um conjunto de `Evidence` candidatas para o pipeline.

A descoberta não resolve identidade funcional. Ela não afirma que duas
evidências representam a mesma pessoa funcional, ainda que tenham sido
localizadas pelo mesmo perfil. Também não normaliza atribuições, não interpreta
atividades, não resolve continuidade e não produz `FunctionalExercise`.

O conjunto de saída pode conter associações com diferentes níveis de confiança.
Cada evidência mantém sua proveniência e sua classificação individual. A
inclusão no conjunto candidato significa somente que há fundamento para
submeter a evidência às etapas posteriores ou à revisão humana.

## 5. Fontes de descoberta

A descoberta pode combinar diversas fontes, desde que a origem de cada
resultado e o critério que o trouxe ao conjunto candidato permaneçam
registrados. Entre as fontes possíveis estão:

- pesquisa textual sobre conteúdo documental;
- índices documentais;
- correspondência de identificadores únicos;
- metadados de documentos;
- conteúdo obtido por OCR;
- catálogos e registros institucionais disponíveis;
- associações previamente confirmadas;
- outras fontes futuras.

Nenhuma fonte é considerada infalível por natureza. Texto extraído por OCR pode
conter erros; metadados podem ser incompletos; identificadores podem estar
ausentes ou registrados incorretamente; nomes podem possuir homônimos.

Este ADR não define algoritmos, precedência técnica entre fontes nem tecnologia
de consulta. Define apenas que múltiplas fontes podem contribuir para a
descoberta e que suas contribuições devem permanecer distinguíveis e
auditáveis.

## 6. Modos de inicialização

### Modo A — Reconstrução iniciada por pessoa

O usuário ou outro fluxo informa o que conhece sobre a pessoa, como nome,
SIAPE, CPF, matrícula ou contexto institucional. Essas informações formam um
`Identity Profile` inicial. `Evidence Discovery` utiliza o perfil para localizar
documentos e produzir evidências candidatas.

O perfil inicial pode ser mínimo. Possuir somente um nome não impede o início
da descoberta, mas tende a produzir confiança menor, mais candidatos ou
ambiguidades que exigem confirmação.

### Modo B — Reconstrução iniciada por documento

O usuário abre, por exemplo, uma portaria que menciona vários servidores e
seleciona uma das pessoas registradas. Os atributos disponíveis nessa menção
formam o `Identity Profile` inicial. A descoberta utiliza esse perfil para
procurar outras evidências no acervo, além da evidência que originou a
inicialização.

A seleção no documento define a pessoa de interesse para a descoberta, mas não
resolve antecipadamente a identidade funcional de todas as ocorrências
encontradas.

Novos modos poderão existir, como inicialização a partir de cadastro
institucional, processo administrativo ou conjunto previamente selecionado de
documentos. Todos devem convergir para um `Identity Profile` explícito e
preservar a mesma separação entre descoberta e reconstrução.

## 7. Confiança

`Evidence Discovery` pode classificar a associação de cada evidência candidata
ao `Identity Profile` como:

- **Alta confiança:** os sinais disponíveis oferecem associação forte e não
  apresentam conflito conhecido relevante;
- **Média confiança:** há sinais consistentes, mas faltam elementos suficientes
  para a classificação mais forte ou existem limitações conhecidas;
- **Baixa confiança:** a associação se apoia em sinais fracos, indiretos ou
  incompletos e requer cautela;
- **Ambígua:** existem associações concorrentes plausíveis, conflitos ou
  insuficiência que impedem escolher uma pessoa com segurança.

O nível de confiança qualifica a associação de descoberta. Ele não confirma
identidade funcional, não mede a veracidade do conteúdo da evidência e não
indica a probabilidade de existência de um fato profissional.

Resultados ambíguos não devem ser resolvidos automaticamente. O sistema pode
solicitar confirmação do usuário, preservando as opções apresentadas, os dados
que fundamentaram a confirmação e a autoria dessa intervenção. A confirmação
permite aceitar ou rejeitar a associação para a descoberta, mas não substitui
a resolução de identidade dentro do pipeline.

Os significados dos níveis e os critérios que sustentam sua atribuição devem
ser estáveis, explicáveis e versionados. Um valor numérico, se futuramente
utilizado, não poderá ocultar os fundamentos qualitativos da classificação.

## 8. Evolução do Identity Profile

O `Identity Profile` pode ser enriquecido durante o uso. Uma primeira
reconstrução pode começar apenas com o nome. Evidências posteriormente
localizadas ou confirmações do usuário podem revelar SIAPE, CPF, matrículas,
instituições relacionadas ou outros nomes utilizados pela pessoa.

Novos atributos podem ser incorporados ao perfil quando sua origem, confiança
e forma de confirmação estiverem registradas. A simples ocorrência de um valor
em uma evidência de baixa confiança ou ambígua não autoriza sua promoção
automática a identificador confirmado, pois isso poderia ampliar buscas futuras
com base em uma associação incorreta.

O enriquecimento pode iniciar novas descobertas e ampliar o conjunto de
evidências candidatas. Deve ser possível distinguir o perfil utilizado em cada
ciclo, os atributos acrescentados e os resultados obtidos.

A evolução do perfil nunca altera fatos históricos. Um atributo novo pode
motivar uma nova descoberta ou uma reconstrução identificável, mas não
reescreve silenciosamente documentos, evidências, `FunctionalExercise` ou
`CareerTimeline` já produzidos.

## 9. Relação com o Pipeline

A relação conceitual completa passa a ser:

```text
Identity Profile
    ↓
Evidence Discovery
    ↓
Evidence
    ↓
Pipeline de Reconstrução Funcional
```

O Blueprint continua válido: sua primeira entrada permanece `Evidence` e suas
responsabilidades internas não mudam. `Evidence Discovery` apenas antecede o
pipeline e entrega um conjunto candidato para processamento.

Essa fronteira também preserva a possibilidade de o pipeline receber
evidências por outras origens legítimas. A reconstrução não precisa conhecer o
mecanismo de busca que produziu a entrada; precisa apenas receber evidências
rastreáveis e manter a incerteza associada.

Descoberta e resolução de identidade respondem a perguntas diferentes:

- descoberta pergunta quais evidências podem estar relacionadas à pessoa de
  interesse;
- resolução pergunta quais evidências normalizadas representam a mesma
  identidade funcional.

Uma associação forte na descoberta não elimina a segunda pergunta, e uma
associação fraca não pode ser fortalecida silenciosamente pelas etapas
posteriores.

## 10. Relação com outros ADRs

### Domain Vision

A [Visão do Domínio](../domain-vision.md) estabelece que documentos fornecem
evidências, fatos profissionais são reconstruídos a partir delas e normas
interpretam posteriormente esses fatos. Este ADR acrescenta a etapa que
seleciona evidências candidatas sem antecipar a reconstrução factual.

### ADR-003 — FunctionalAssignmentNormalizer

O [ADR-003](ADR-003-functional-assignment-normalizer.md) recebe uma
`FunctionalAssignmentEvidence` já formada e normaliza suas representações.
`Evidence Discovery` atua antes dela, sobre a localização e associação inicial
de `Evidence`. Descoberta não normaliza nomenclaturas e normalização não procura
novas evidências.

### ADR-004 — Functional Activity Taxonomy

O [ADR-004](ADR-004-functional-activity-taxonomy.md) define a linguagem
canônica das atividades funcionais. A descoberta não utiliza essa taxonomia
para decidir quais atividades uma pessoa exerceu. Cargos conhecidos no perfil
servem somente como pistas de busca e não constituem classificação funcional.

### Blueprint do Pipeline de Reconstrução Funcional

O [Blueprint](../functional-reconstruction-pipeline.md) permanece a definição
do fluxo que começa em `Evidence`. Este ADR define a etapa anterior que produz
o conjunto candidato. Ele também esclarece que o `IdentityResolver` descrito no
Blueprint não deve absorver responsabilidades de busca ou formação do perfil.

O Blueprint originalmente indicou Identity Resolution como ADR-005. Com a
formalização desta etapa antecedente como ADR-005, a sequência prospectiva
passa a reservar os números seguintes para:

- **ADR-006 — Identity Resolution:** equivalência, conflito e ambiguidade entre
  identidades funcionais;
- **ADR-007 — Functional Activity Resolution:** correspondência entre
  evidências e a taxonomia funcional;
- **ADR-008 — Continuity Resolution:** continuidade, interrupção, sobreposição
  e limites temporais.

Essa atualização de sequência não altera o pipeline nem antecipa as decisões
desses ADRs.

## 11. Fora do escopo

Este ADR não define:

- algoritmo de matching;
- algoritmo de OCR;
- algoritmo de busca;
- implementação;
- entidades, classes ou interfaces;
- contratos de software;
- banco de dados;
- formato de persistência;
- interface gráfica;
- políticas detalhadas de proteção de dados pessoais;
- critérios de Identity Resolution;
- classificação de atividades funcionais;
- resolução de continuidade;
- interpretação normativa;
- pontuação ou efeitos jurídicos.

## Decisões aprovadas

- `Identity Profile` e `Evidence Discovery` são conceitos independentes.
- Ambos pertencem à etapa anterior ao pipeline de reconstrução funcional.
- O perfil representa conhecimento para descoberta, não trajetória ou fatos.
- A lista de atributos do perfil é extensível e preserva origem e confiança.
- Cargos, instituições e períodos conhecidos são pistas, não fatos
  reconstruídos.
- A descoberta localiza documentos, extrai evidências relacionadas e classifica
  a confiança de cada associação.
- O conjunto produzido é candidato e não confirma identidade funcional.
- Resultados ambíguos não são resolvidos automaticamente.
- Confirmações humanas são possíveis e devem permanecer auditáveis.
- O perfil pode evoluir sem alterar fatos históricos.
- A ausência de resultados de descoberta não demonstra ausência de trajetória.
- O Blueprint permanece válido e recebe `Evidence` após a etapa antecedente.
- Identity Resolution, Functional Activity Resolution e Continuity Resolution
  permanecem responsabilidades de ADRs posteriores.

## Questões para ADR futuro

- Quais atributos podem estabelecer, reforçar ou contradizer equivalência entre
  identidades funcionais?
- Como diferenciar homônimos quando identificadores únicos estiverem ausentes?
- Como representar identidades candidatas, conflitos e resultados não
  resolvidos?
- Qual é o efeito de uma confirmação humana da descoberta sobre a resolução de
  identidade, sem tornar as duas decisões equivalentes?
- Como tratar identificadores divergentes em evidências aparentemente
  relacionadas?
- Quais informações de proveniência e versão devem acompanhar cada decisão de
  identidade?
- Quando evidências podem ser agrupadas para análise sem que o agrupamento
  antecipe a decisão final de identidade?
