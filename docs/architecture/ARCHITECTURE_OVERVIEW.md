# ProcDocOrganizer — Architecture Overview

## Dashboard 2.0

Na estabilização C-004, Coverage e Insights são compostos uma única vez no Application Service/composition root e compartilhados com Dashboard e Review. O Dashboard não registra Providers. Ações operacionais usam contrato próprio e não Navigation Intent.

O Dashboard é consumidor passivo de `WorkspaceSnapshot`, `CoverageResult` e `InsightCollection`. O serviço coordena os contratos oficiais, o ViewModel projeta DTOs imutáveis e a View apenas renderiza e emite Navigation Intents. Nenhuma métrica, Insight ou regra normativa nasce no Dashboard. Consulte [DASHBOARD_2.md](DASHBOARD_2.md).

## Review Workspace

A fila do Review é composta por Insights; Findings permanecem em Coverage. Seus filtros são `WorkspaceFilter` mantidos em `WorkspaceSnapshot.active_filters`.

O Review Workspace usa Coverage para resumos e Insights ativos para formar uma fila operacional filtrável e determinística. Seus itens armazenam apenas `ResourceIdentity` e emitem Navigation Intents; a atualização do Inspector pertence ao fluxo oficial do Workspace. Consulte [REVIEW_WORKSPACE.md](REVIEW_WORKSPACE.md).

**Escopo:** núcleo RSC
**Release de referência:** Beta 1.1
**Baseline:** Workspace Dashboard
**Status:** referência arquitetural principal

## 1. Visão geral

### 1.1 Objetivo do domínio

O ProcDocOrganizer organiza a reconstrução factual, a comprovação documental
e a avaliação rastreável de um processo de Reconhecimento de Saberes e
Competências (RSC). O sistema preserva a separação entre:

1. fonte documental;
2. interpretação factual;
3. medição estruturada;
4. aplicação normativa;
5. cálculo aritmético;
6. consolidação e apresentação do resultado.

Essa separação impede que um documento seja tratado automaticamente como fato,
que um fato seja confundido com critério atendido ou que uma pontuação apague
as evidências e decisões que a originaram.

### 1.1.1 P-001 — Avaliação Progressiva

> O ProcDocOrganizer deve ser capaz de produzir avaliações parciais sempre
> que possível. Pendências operacionais não devem impedir a compreensão do
> estado do processo. Somente falhas que impossibilitem tecnicamente a
> execução do Pipeline poderão interromper a avaliação.

Um `ExecutionFact` sem `ExecutionBinding` é pendência operacional. Ele integra
o snapshot do processo, mas não é entregue a Validation, Compatibility ou
Kernel até receber enquadramento explícito.

### 1.2 Base da plataforma

A base da plataforma, concentrada principalmente em `core/`, fornece:

- registro e resolução de aplicações;
- ciclo de vida do host;
- runtime e sessões;
- contexto, estado e controle de projetos;
- contribuição de aplicações à plataforma.

A plataforma conhece contratos gerais de aplicação, projeto e sessão. Ela não
conhece critérios RSC, pontuação, evidências funcionais ou o Decreto.

### 1.3 Aplicação RSC

`applications/rsc/` contém o domínio e a aplicação específica de RSC:

- entidades, Aggregate Roots e Value Objects;
- comandos, casos de uso, serviços e DTOs;
- pipeline factual e normativo;
- catálogo normativo executável;
- contratos de execução, Kernel e agregação;
- `RSCProcess`, que preserva os snapshots do processo completo;
- portas de persistência e implementações de infraestrutura específicas.

### 1.4 Infraestrutura

A infraestrutura implementa detalhes substituíveis:

- container de projeto `.pdop`;
- serializers e migração de schema;
- repositories em memória e SQLite;
- arquivos documentais;
- resolução de caminhos e disponibilidade de fontes.

Infraestrutura implementa portas definidas pela aplicação. Ela não define
invariantes do domínio nem regras normativas.

### 1.5 Interface

`presentation/` mantém estado, seleção, perspectivas, navegação, operações,
notificações, controllers e projeções da camada de apresentação. `ui/` contém
componentes visuais concretos.

A interface consome APIs, DTOs, controllers e projeções. Widgets não acessam
SQLite, repositories ou Aggregate Roots para alterar estado diretamente.

## 2. Camadas

O fluxo lógico de controle é:

```text
UI
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

Infrastructure aparece abaixo do domínio como detalhe técnico, mas a
dependência de código é invertida: a aplicação declara portas e a
infraestrutura as implementa.

### 2.1 UI

Responsabilidades:

- capturar intenção do usuário;
- apresentar projeções e estados;
- coordenar seleção e navegação;
- exibir progresso, notificações e falhas;
- delegar operações a controllers e à API pública.

Pode depender de Application. Não pode conter regra de negócio, cálculo
normativo, acesso direto a banco ou ciclo de vida próprio de entidades.

### 2.2 Application

Responsabilidades:

- casos de uso e coordenação transacional;
- services, controllers de aplicação e Facade;
- construção de snapshots;
- validação de referências entre agregados;
- composição do pipeline;
- declaração de portas;
- tradução entre domínio, DTOs e infraestrutura.

Pode depender de Domain e de abstrações estáveis. Não pode depender de
widgets, MainWindow ou detalhes concretos de armazenamento.

### 2.3 Domain

Responsabilidades:

- identidade e ciclo de vida das entidades;
- invariantes locais dos Aggregate Roots;
- Value Objects e estados;
- relações por identidade entre agregados;
- resultados imutáveis do domínio.

Não conhece UI, banco, filesystem, Qt, repositories concretos ou detalhes do
container `.pdop`.

### 2.4 Infrastructure

Responsabilidades:

- persistência e reidratação;
- transações e schema físico;
- serialização e migração;
- integração com arquivos e recursos externos.

Pode depender das portas e modelos que implementa. Não pode fazer o domínio
depender de SQLite, ZIP, caminhos físicos ou schemas.

### 2.5 Dependências proibidas

- Domain → UI, Qt, SQLite, filesystem ou repositories concretos;
- Kernel → Decreto, catálogo, repositories, Aggregate Roots ou UI;
- UI → SQLite ou manipulação direta de Aggregate Roots;
- Aggregate Root → outro Aggregate Root por referência de objeto mutável;
- Validation → regra de compatibilidade normativa;
- Compatibility → cálculo de pontuação;
- Infrastructure → criação de regra de negócio;
- catálogo → estado factual de um processo.

A `MainWindow` é o único shell produtivo. A composition root iniciada por
`app.py` monta explicitamente o Workspace produtivo e o
`ProjectExplorerApplicationService`; o Project Explorer permanece uma
perspectiva operacional hospedada pelo shell e o módulo visual não importa
SQLite.

### 2.6 Workspace Dashboard

O Dashboard é a tela inicial de um projeto aberto e segue o fluxo
`Project → WorkspaceDashboardService → WorkspaceDashboardViewModel → DTOs →
WorkspaceDashboardView`. O serviço consolida exclusivamente informações
operacionais e reapresenta pontuação já produzida por uma avaliação; não
executa Pipeline, não acessa Kernel e não recalcula resultados.

A View consome somente DTOs imutáveis de apresentação e emite intenções de
navegação. Ela não conhece agregados, scores, stores ou SQLite. O Project
Explorer liga essas intenções ao fluxo `Dashboard → Project Explorer →
Evaluation → Results → Evaluation Report`. Detalhes constam em
[WORKSPACE_DASHBOARD.md](WORKSPACE_DASHBOARD.md).

### 2.7 Presentation Workspace Navigation

A ADR-034 evolui a infraestrutura existente sem criar mecanismo paralelo.
Views emitem `NavigationIntent` tipada; o `NavigationController` atua como
Navigation Service e coordena uma transição publicada atomicamente pelo
`PresentationContextStore`. O `WorkspaceSnapshot` contém somente IDs e estado
de apresentação imutável, incluindo perspectiva, seleção e filtros.

Os contratos não dependem de Qt, Web, CLI, domínio ou persistência. O histórico
linear registra a Intent e o snapshot resultante. Um cursor oferece voltar,
avançar e restaurar a entrada atual; restaurações usam o snapshot como
autoridade, não repetem a Intent e não criam novas entradas. Nova navegação
após voltar descarta o ramo futuro.

### 2.7.1 Shell produtivo

O fluxo real é `app.py → Application → MainWindow`. A composition root registra
explicitamente `workspace_dashboard`, `review_workspace`, `project_explorer`,
`results` e `evaluation_report`, preservando as perspectivas legadas. Intents
de Resource são roteadas para o Project Explorer; Evaluation e Report são
perspectivas próprias. Todas as transições passam pelo mesmo
`NavigationController`.

### 2.8 Resource Infrastructure

A ADR-035 define Resource como a única projeção navegável da apresentação.
`ResourceIdentity` separa tipo e identificador dos dados de exibição;
`ResourceRelationship` aponta somente para outra identidade; e
`PresentationAction` declara capacidades sem executá-las.

Resources são DTOs imutáveis produzidos pelo contrato `ProjectionService`.
Os projetores iniciais de Document, Evidence e Requirement são neutros e
independentes de toolkit, domínio e persistência. `ResourceCollection`
representa resultados de consulta e não constitui Resource ou Aggregate.

O Workspace preserva somente identidades, nunca Resources completos. A
infraestrutura está detalhada em
[RESOURCE_INFRASTRUCTURE.md](RESOURCE_INFRASTRUCTURE.md).

### 2.9 Resource Inspector

O Resource Inspector consome Resources por meio do fluxo `Workspace Snapshot
→ ResourceIdentity → ProjectionService → Resource → ViewModel → View`. A
composition root resolve o projetor para Document, Evidence ou Requirement e
atualiza o Inspector quando o contexto consolidado muda.

O ViewModel cria DTOs imutáveis e Navigation Intents. A View apenas renderiza
esses DTOs e emite as Intents, sem acessar Stores, domínio, persistência,
Projection Services ou outras Views. Estados vazios, projeções indisponíveis e
seções sem conteúdo são apresentados explicitamente.

Detalhes constam em [RESOURCE_INSPECTOR.md](RESOURCE_INSPECTOR.md).

### 2.10 Workspace Insights

A ADR-036 define Insight como projeção imutável, explicável, derivada e não
persistente de uma condição do Workspace. `InsightIdentity` estabiliza origem,
código e discriminador; referências apontam apenas para `ResourceIdentity`; e
categorias, severidades e ações possuem finalidade de apresentação.

`WorkspaceInsightProvider` produz Insights para uma revisão específica. O
`WorkspaceInsightService` coordena Providers explicitamente registrados,
valida origem e revisão, rejeita identidades duplicadas e produz uma
`InsightCollection` deterministicamente ordenada.

A fundação inicial contém apenas `ProjectEvaluationInsightProvider`. Não há
integração com Dashboard, Inspector ou qualquer View. Detalhes constam em
[WORKSPACE_INSIGHTS.md](WORKSPACE_INSIGHTS.md).

### 2.11 Coverage Analyzer

A ADR-037 estabelece Coverage como análise observacional estruturada. Um
`CoverageInput` imutável normaliza referências operacionais; o
`CoverageAnalyzer` produz `CoverageResult` com escopos Document, Evidence,
Factual, Normative e Overall, além de Findings explicáveis.

Estados normativos são somente contados e preservados como recebidos. Sem
Evaluation, a cobertura normativa é `NOT_EVALUATED`. A cobertura geral utiliza
contagens e razão exata, sem média ou percentual autoritativo. Não existe
integração visual ou com Insights nesta etapa.

Detalhes constam em [COVERAGE_ANALYZER.md](COVERAGE_ANALYZER.md).

## 3. Pipeline factual e normativo

O fluxo executável completo é:

```text
Evidence
   ↓ interpretação e construção factual
ExecutionFact
   ├─ sem Binding → pendência preservada no RSCProcess
   └─ com Binding → ExecutionValidator
ExecutionValidation
   ↓ ExecutionCompatibilityEvaluator
ExecutionCompatibility
   ↓ ExecutionContractResolver
CriterionExecutionContract
   ↓ CriterionScoringKernel
CriterionScore
   ↓ RequirementScoreAggregator
RequirementScore
   ↓ registro de snapshots
RSCProcess
```

### 3.1 Evidence

Produzida por casos de uso documentais ou por ação explícita do usuário.
Preserva a origem documental e é consumida pela reconstrução funcional. Não
constitui, por si só, confirmação de atividade ou satisfação de critério.

### 3.2 ExecutionFact

Produzido por `ExecutionFactBuilder` a partir do `EvaluationContext` e das
análises anteriores. É o fato canônico e observável entregue ao trecho
executável do motor. Contém `Measurement`, ocorrências, referências canônicas
e rastreabilidade factual e normativa.

### 3.3 ExecutionValidation

Produzida por `ExecutionValidator`. Responde exclusivamente se o fato está
completo e internamente consistente. Registra ausências e inconsistências.
Não decide se a Measurement é adequada a uma regra normativa.

### 3.4 ExecutionCompatibility

Produzida por `ExecutionCompatibilityEvaluator`. Compara a Measurement do
fato à política do critério obtida do catálogo. É a única etapa responsável
pela compatibilidade entre medição e regra. Não recalcula fatos nem pontua.

### 3.5 CriterionExecutionContract

Produzido por `ExecutionContractResolver`. Consolida fato, validação,
compatibilidade, regra, valor normativo resolvido e rastreabilidade em um
contrato autocontido. O Kernel não precisa consultar outro componente.

### 3.6 CriterionScore

Produzido por `CriterionScoringKernel`. Registra estado, quantidade,
operando normativo, operação Decimal, resultado, trace e explicação. Contratos
bloqueados também produzem Score; o Kernel nunca retorna ausência silenciosa.

### 3.7 RequirementScore

Produzido por `RequirementScoreAggregator`. Agrupa `CriterionScore` por
requisito e soma apenas resultados `EXECUTED`, preservando executados,
bloqueados e ignorados.

### 3.8 RSCProcess

Recebe e preserva cada coleção produzida. Controla a sequência dos snapshots,
valida continuidade de identidades e expõe resultado, pendências, alertas e
evidências. Não invoca o pipeline nem executa cálculo.

> O pipeline histórico de candidatos, qualificação documental, constraints e
> assessments continua responsável por preparar a análise anterior ao
> `ExecutionFact`. Ele não substitui o fluxo executável descrito acima.

## 4. Aggregate Roots

O repositório possui gerações de modelos que coexistem por compatibilidade.
Os nomes abaixo distinguem o modelo factual atual, o domínio normativo legado
e a orquestração introduzida na Release 2.5.

### 4.1 RSCProcess — orquestração completa

- **Responsabilidade:** preservar os snapshots e a progressão de um processo
  RSC completo.
- **Identidade:** `aggregate_id`, correspondente ao `process_id`.
- **Invariantes:** identidade estável; estágio sequencial; critérios existentes
  no catálogo; correspondência integral entre fatos e resultados; ausência de
  duplicidades; referências internas válidas.
- **Ciclo:** `DRAFT → EVIDENCE → FACTS → VALIDATED → COMPATIBLE → SCORED →
  AGGREGATED → CONSOLIDATED`.
- **Revisão:** cada transição retorna novo snapshot e incrementa `revision`.
  Retenção e reconstrução cronológica pertencem à persistência.

### 4.2 Project — contexto de trabalho

- **Responsabilidade:** delimitar o projeto, sua sessão e os elementos
  manipulados pelos casos de uso.
- **Identidade:** `project_id`.
- **Invariantes:** referências e coleções válidas, preservadas na reabertura.
- **Ciclo:** criação, operação em sessão, persistência e reabertura.

O projeto físico e o processo normativo não são sinônimos: o primeiro delimita
armazenamento e sessão; `RSCProcess` delimita a orquestração da avaliação.

### 4.3 Activity

- **Responsabilidade:** acompanhar uma atividade lembrada até sua comprovação.
- **Identidade:** `activity_id`.
- **Invariantes:** descrição obrigatória; referências únicas; comprovação
  parcial exige evidência funcional; comprovação exige evidência funcional e
  exercício.
- **Ciclo:** `REMEMBERED → UNDER_INVESTIGATION → PARTIALLY_PROVEN → PROVEN`.

### 4.4 Evidence

- **Responsabilidade:** preservar uma afirmação rastreável até sua fonte
  documental.
- **Identidade:** UUID próprio, distinto da identidade do Document.
- **Invariantes:** documento obrigatório; página positiva quando presente;
  campos e datas consistentes; timestamps não regressivos; referência
  histórica preservada.
- **Ciclo:** criação, edição e remoção autorizada independentes dos demais
  agregados.

### 4.5 FunctionalAssignmentEvidence

- **Responsabilidade:** representar uma interpretação funcional estruturada
  de uma Evidence.
- **Identidade:** `FunctionalAssignmentEvidenceId`.
- **Invariantes:** Evidence de origem válida; identidade imutável; dados
  funcionais obrigatórios; datas consistentes; transições explícitas.
- **Ciclo:** `RAW → IDENTIFIED → LINKED`. `NORMALIZED` existe apenas para
  reidratação compatível do legado.

### 4.6 FunctionalExercise

- **Responsabilidade:** representar o exercício funcional reconstruído em
  contexto e período determinados.
- **Identidade:** `FunctionalExerciseId`.
- **Invariantes:** pessoa, tipo, papel, contexto e período válidos; referências
  de evidência sem duplicidade; ativo exige período aberto; encerrado exige
  período fechado.
- **Ciclo:** criação como exercício ativo ou encerrado e evolução explícita de
  período/estado pelos serviços responsáveis.

### 4.7 Document

Document possui identidade, repository e ciclo independente e funciona
operacionalmente como unidade de consistência documental. O modelo de domínio
1.0 ainda o classifica como Aggregate Root operacional não formalizado. Esta
visão preserva essa ressalva: nenhuma outra raiz controla ou modifica seu
ciclo.

### 4.8 Modelo normativo legado

`RscProcess`, `RscActivity`, `RscEvidence`, `RscDocument`, `RscCriterion` e
`RscRequirement`, em `applications/rsc/domain/`, formam a geração normativa
anterior ainda preservada por compatibilidade. Eles não devem ser confundidos
automaticamente com `RSCProcess`, `Activity`, `Evidence` e os contratos do
pipeline atual. A convergência dessas APIs exige decisão própria e não é
realizada neste documento.

### 4.9 Não são Aggregate Roots

`Category`, `Institution`, `Person` canônica, `Report`, Timeline,
`CriterionScore`, `RequirementScore`, validações, contratos, catálogo,
Measurements e objetos de trace não possuem ciclo transacional autônomo no
modelo atual.

## 5. Value Objects e snapshots imutáveis

### 5.1 Identidade e referência

- `FunctionalAssignmentEvidenceId`;
- `FunctionalExerciseId`;
- `SourceEvidenceReference`;
- IDs de processo, projeto, atividade, documento, Evidence, critério,
  requisito, contrato, validação e Score;
- referências canônicas e opacas a objetos de outros agregados.

IDs não transferem propriedade. Associações entre agregados são unidirecionais
e coordenadas pela aplicação.

### 5.2 Valores funcionais

- `FunctionalExerciseType`;
- `FunctionalRole`;
- `FunctionalContext`;
- `FunctionalPeriod`;
- estados de Activity, interpretação funcional e exercício.

São normalizados, comparáveis por valor e não possuem identidade própria.

### 5.3 Contexto de avaliação

`EvaluationProject`, `EvaluationActivity`,
`EvaluationFunctionalExercise`,
`EvaluationFunctionalAssignmentEvidence`, `EvaluationEvidence` e
`EvaluationDocument` compõem `EvaluationContext`, snapshot somente leitura da
cadeia factual. Eles não substituem Aggregate Roots nem permitem mutação.

### 5.4 Fatos executáveis

- `FactTraceability` e `CanonicalFact`;
- `CanonicalDocument`, `CanonicalActivity` e
  `CanonicalFunctionalExercise`;
- `CanonicalTimeInterval`;
- `Measurement`;
- `ExecutionOccurrence`;
- `ExecutionNormativeTraceability`;
- `ExecutionFact` e suas coleções imutáveis.

`Measurement` preserva a informação originalmente disponível. Valores
normativamente derivados não são materializados antecipadamente nela.

### 5.5 Validação e compatibilidade

- `MissingFact`, `MissingDocument`, `MissingVariant`,
  `MissingMeasurement` e `InconsistentFact`;
- `ExecutionValidationTraceability`;
- `ExecutionValidation`;
- `ExecutionCompatibility`.

Esses objetos descrevem resultados intermediários; não possuem ciclo próprio.

### 5.6 Contrato e valor normativo

- `ResolvedCountingRule`;
- `ResolvedVariantRule`;
- `NormativeValueTraceability`;
- `ResolvedNormativeValue`;
- `CriterionExecutionContract`;
- `CompatibilityPolicy`;
- `NormativeValueVariant`;
- `NormativeCriterionDefinition`.

São autocontidos, rastreáveis e imutáveis. Valores numéricos normativos usam
`Decimal`.

### 5.7 Cálculo e consolidação

- `TemporalDecomposition`;
- `ScoringExecutionTrace`;
- `CriterionScore`;
- `RequirementAggregationTrace`;
- `RequirementScore`;
- `TemporalAttention`;
- `RSCServer`, `RSCInstitution`, `RSCProcessEvidence` e `RSCProcessResult`.

Scores são resultados, não entidades. A igualdade estrutural dos snapshots
não substitui a identidade explícita de um Aggregate.

### 5.8 Imutabilidade

Os Value Objects e snapshots do pipeline são `dataclass(frozen=True)` e, em
geral, `slots=True`. Coleções usam tuplas. Cada etapa produz novos objetos e
preserva os anteriores, permitindo repetibilidade, auditoria e comparação
estrutural.

## 6. Services

### 6.1 Existentes

| Serviço/componente | Responsabilidade |
|---|---|
| `ActivityManagementService` | CRUD e ciclo da Activity |
| `FunctionalAssignmentManagementService` | CRUD e transições da interpretação funcional |
| `FunctionalExerciseManagementService` | CRUD e ciclo do exercício |
| `DocumentService` / `DocumentHealthService` | gestão documental e diagnóstico de fontes |
| `EvidenceService` | operações de Evidence |
| `ProcessService` | operações do processo normativo legado |
| `ValidationService` | fachada de validação do domínio legado |
| `ScoringService` | fachada de pontuação do domínio legado |
| serviços `Create*` e `List*` | casos de uso focados de criação e consulta |
| `EvaluationContextBuilder` | monta snapshot factual consultando repositories |
| `ExecutionFactBuilder` | converte assessment e contexto em fatos canônicos |
| `ExecutionValidator` | valida completude e consistência factual |
| `ExecutionCompatibilityEvaluator` | decide compatibilidade Measurement/regra |
| `ExecutionContractResolver` | monta contrato executável autocontido |
| `CriterionScoringKernel` | executa somente aritmética autorizada |
| `RequirementScoreAggregator` | consolida Scores por requisito |
| `TemporalAttentionAnalyzer` | produz alertas informativos sem efeito no cálculo |

Candidate Engine, Evidence Qualification, Constraint Evaluation e Criterion
Assessment permanecem componentes existentes do pipeline de preparação e
explicabilidade anterior à execução.

### 6.2 Planejados

- Application Service do processo completo, para compor o pipeline sem mover
  responsabilidades para `RSCProcess`;
- repository e unidade de persistência versionada dos snapshots do processo;
- serviço de importação documental;
- adapters de OCR e parsing;
- serviços assistidos por IA com saída revisável e nunca normativa por si só;
- API externa e serviço de relatórios.

Serviços planejados devem consumir contratos existentes, não acessar estado de
widgets e não transferir lógica normativa para infraestrutura.

## 7. Catálogo normativo

### 7.1 NormativeCriterionCatalog

É a única fonte normativa executável. Contém 55 definições imutáveis do
Decreto nº 13.048/2026 e rejeita códigos, regras ou combinações inválidas. O
Decreto permanece a fonte jurídica; o catálogo é sua projeção computável.

### 7.2 Measurement

Tipos consolidados incluem `QUANTITY`, `COUNT`, `HOURS` e `DURATION`.
Computabilidade é autodescritiva:

- valores quantitativos exigem `measurement.amount`;
- `DURATION` exige intervalo canônico completo e não exige `amount`;
- tipo sem política explícita é não computável.

### 7.3 Compatibility

`CompatibilityPolicy` declara Measurements admitidas. A política pertence ao
catálogo e é consumida exclusivamente por `ExecutionCompatibilityEvaluator`.
Validation e Kernel não duplicam essa decisão.

### 7.4 Arithmetic Engine

`ArithmeticEngine` classifica a família computacional. O contrato entrega
motor, quantidade factual ou intervalo, operando e regras resolvidas. O
Kernel conhece operações aritméticas suportadas, não códigos do Decreto.

### 7.5 Value Variants

`NormativeValueVariant` representa valores alternativos explícitos, como
papéis ou modalidades previstos pela norma. Uma definição usa valor fixo ou
variantes, nunca ambos. A resolução ocorre antes do Kernel e conserva base
legal e trace.

## 8. Infraestrutura temporal

### 8.1 Decomposição temporal canônica

`TemporalDecomposition` preserva:

- início e fim;
- anos completos;
- meses residuais;
- dias residuais;
- indicação da fração de seis meses;
- total derivado de meses completos.

Toda regra temporal consome essa decomposição. Nenhuma regra implementa
algoritmo próprio de datas.

### 8.2 PER_YEAR

Usa anos-calendário completos. Período menor que um ano produz zero; período
aberto, inválido, invertido, sobreposto ou com múltiplas ocorrências não
suportadas fica bloqueado.

### 8.3 PER_MONTH

Usa `complete_years × 12 + residual_months`. Dias residuais são preservados
para explicação e não produzem mês adicional.

### 8.4 FRACTION_ABOVE_SIX_MONTHS

Após os anos completos, resíduo igual ou superior a seis meses-calendário
acrescenta exatamente um ano. O incremento é somente `+0` ou `+1`, inclusive
quando não há ano completo.

### 8.5 Regras e alertas

Datas de 29 de fevereiro usam o tratamento canônico documentado. Operações
usam `Decimal`; `float` não participa do cálculo. `TemporalAttentionAnalyzer`
reutiliza a decomposição para orientar revisão humana, mas jamais altera
contrato, estado, quantidade ou pontuação.

## 9. Princípios arquiteturais

1. O domínio não conhece UI.
2. O domínio não conhece banco, filesystem ou formato de container.
3. A UI não acessa banco diretamente.
4. O Kernel não conhece o Decreto nem códigos específicos de critérios.
5. O catálogo é a única fonte normativa executável.
6. `ExecutionFact` é a entrada factual do trecho executável do motor.
7. Validation verifica fatos; Compatibility verifica adequação normativa.
8. O contrato é autocontido; o Kernel não procura informações.
9. O Aggregate `RSCProcess` apenas orquestra e preserva snapshots.
10. Snapshots e resultados do pipeline são imutáveis.
11. Igualdade estrutural não equivale à identidade do Aggregate.
12. `aggregate_id` identifica o processo entre revisões.
13. Reconstrução cronológica pertence à persistência.
14. Relações entre Aggregate Roots usam identidades, não propriedade mutável.
15. Nenhuma etapa silenciosamente descarta bloqueios, pendências ou trace.
16. Cálculos oficiais usam `Decimal`, nunca `float`.
17. Valores derivados da norma não contaminam fatos observáveis.
18. Toda regra temporal consome a decomposição temporal canônica.

## 10. Extensibilidade

### 10.1 Novo critério

1. extrair e rastrear a fonte jurídica;
2. criar código estável e definição no catálogo;
3. informar requisito, família, unidade, Measurement, política e motor;
4. declarar valor fixo ou variantes;
5. registrar limites, dependências, revisão humana e explicabilidade;
6. validar unicidade, compatibilidade e cobertura;
7. não adicionar condicional específica ao Kernel.

### 10.2 Nova política

1. justificar a combinação normativa;
2. criar identificador controlado;
3. declarar Measurements admitidas;
4. associar motores compatíveis;
5. estender testes do catálogo e de Compatibility;
6. manter Validation e Kernel inalterados sempre que a aritmética existente
   for suficiente.

### 10.3 Nova Measurement

1. definir semântica factual e unidade;
2. declarar política explícita de computabilidade;
3. especificar dados mínimos e rastreabilidade;
4. definir compatibilidades no catálogo;
5. adaptar Builder, Validation e contratos sem antecipar interpretação;
6. implementar aritmética somente se nenhuma operação existente servir.

### 10.4 Novo tipo documental

1. registrar identidade e metadados documentais;
2. preservar arquivo e hash sem inferir fato;
3. declarar categoria aceita no catálogo quando houver base normativa;
4. adaptar importador/parser por porta de infraestrutura;
5. manter Evidence e referências históricas independentes da disponibilidade
   física;
6. adicionar projeções de UI sem acesso direto ao armazenamento.

## 11. Roadmap

### 11.1 Application Service

Compor Builder, Validation, Compatibility, Resolver, Kernel, Aggregator,
alertas e transições do `RSCProcess` em uma operação transacional explícita.

### 11.2 Persistência

Definir repository de snapshots, schema versionado, atomicidade, reabertura e
histórico por `aggregate_id` e `revision`, sem encadear revisões dentro do
Aggregate.

### 11.3 Desktop

Integrar o processo aos Stores, controllers, WorkspaceHost, notificações e
navegação existentes, mantendo widgets passivos.

### 11.4 Importação

Criar ingestão manual assistida, deduplicação e mapeamento de metadados por
adapters substituíveis.

### 11.5 OCR

Implementar OCR como processamento derivado e reexecutável. Texto reconhecido
não substitui o arquivo original nem confirma fato automaticamente.

### 11.6 IA

Adicionar sugestões explicáveis, com proveniência, confiança, revisão humana
e impossibilidade de alterar norma ou pontuação diretamente.

### 11.7 API

Expor comandos e queries estáveis, autenticação, versionamento e DTOs sem
vazar Aggregate Roots, schemas SQLite ou detalhes do desktop.

## 12. Decisões arquiteturais consolidadas

| Decisão | Consequência |
|---|---|
| Catálogo substitui conhecimento normativo disperso | critérios são parametrizados; Kernel permanece genérico |
| Compatibility é independente de Validation e Kernel | cada componente responde a uma única pergunta |
| Measurement possui computabilidade por tipo | não existe requisito universal de `amount` |
| Neutralidade factual | anos, meses e quantidades normativas não surgem antes do Kernel |
| Contrato executável é autocontido | Kernel não consulta catálogo, repositories ou pipeline |
| Infraestrutura temporal é canônica | regras não duplicam manipulação de datas |
| Cálculo usa Decimal | resultados são determinísticos e preservam precisão |
| Scores preservam bloqueios e trace | não há perda silenciosa de informação |
| Requirement aggregation soma somente executados | estados não executáveis permanecem auditáveis |
| RSCProcess é imutável | cada alteração produz novo snapshot |
| Identidade é explícita por `aggregate_id` | revisões distintas continuam sendo o mesmo processo |
| Igualdade do dataclass é estrutural | snapshots diferentes não são confundidos |
| Histórico pertence à persistência | Aggregate não aponta para revisão anterior |
| Relações entre agregados são por identidade | ciclos de vida e fronteiras transacionais permanecem independentes |
| UI trabalha por Stores, controllers e projeções | estado visual não se torna fonte de verdade |
| Infraestrutura implementa portas | detalhes técnicos não governam o domínio |
| `ApplicationLifecycleHost` é a autoridade do Project ativo | Controller, View e serviços não mantêm lifecycle paralelo |
| Ativação de sessão é transacional | falhas preservam sessão, Workspace e consumidores anteriores |
| Serviços produtivos são project-scoped | todos operam sobre o `database.db` do `.pdop` ativo |
| `DocumentRepository` é o catálogo documental | Documents independentes chegam ao Coverage |
| Revisões operacional, visual e de Evaluation são distintas | nenhuma revisão é inferida de outra |

Detalhes do lifecycle consolidado, rollback, revisão operacional e tratamento
do banco produtivo legado estão em `PROJECT_AUTHORITY.md`.

## Estado e recomendações

O núcleo já possui cadeia factual e normativa rastreável, catálogo com
cobertura oficial, compatibilidade separada, Kernel determinístico,
consolidação por requisito e Aggregate de processo completo. As prioridades
arquiteturais seguintes são:

1. criar o Application Service de composição do processo;
2. persistir snapshots por identidade e revisão;
3. definir a convergência controlada entre modelos legados e atuais;
4. formalizar Document como Aggregate Root ou registrar definitivamente sua
   condição operacional;
5. manter gates que impeçam regras do Decreto no Kernel e acesso da UI ao
   armazenamento;
6. versionar o catálogo e sua proveniência antes de múltiplas normas.
