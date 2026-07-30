# Matriz de Rastreabilidade do Pipeline Normativo

## 1. Cadeia factual

| Origem | Campo de ligação | Destino | Verificação |
|---|---|---|---|
| Document | `document_identity` | Evidence | Builder e contexto |
| Evidence | `id` | FunctionalAssignmentEvidence | Builder e contexto |
| FunctionalAssignmentEvidence | `id` | FunctionalExercise | Builder e contexto |
| FunctionalExercise | `id` | Activity | Builder e contexto |
| Activity/Exercise | IDs no metadata | CriterionCandidate | Candidate Engine |

O domínio armazena relações no sentido Activity → Exercise → Assignment →
Evidence → Document. A leitura inversa da tabela acima é possível por
identidades, mas não há índice reverso público.

## 2. Cadeia normativa

| Estágio | Origem preservada |
|---|---|
| CriterionCandidate | `NormativeOrigin` do critério |
| EvidenceQualification | origem do candidato e referência da categoria |
| ConstraintEvaluation | origem de cada condição e fatos utilizados |
| CriterionAssessment | origem normativa, condições e verificações |

## 3. Matriz ponta a ponta

| Informação | Context | Candidate | Qualification | Constraint | Assessment |
|---|:---:|:---:|:---:|:---:|:---:|
| Document ID | ✓ | ✓ uma origem | ✓ todas recuperadas | via qualificação | ✓ |
| Identidade documental | ✓ | ✓ | ✓ | via qualificação | ✓ |
| Evidence ID | ✓ | ✓ | via candidato | via candidato | via origem factual |
| Assignment ID | ✓ | ✓ | via candidato | via candidato | via origem factual |
| Exercise ID | ✓ | ✓ | ✓ | ✓ | ✓ |
| Activity ID | ✓ | ✓ | ✓ | ✓ | ✓ |
| Criterion ID | metadata | ✓ | ✓ | ✓ | ✓ |
| Requirement ID | modelo | ✓ | ✓ | ✓ | ✓ |
| Categoria documental | metadata/modelo | opcional | ✓ | via qualificação | via fonte |
| Dispositivo do critério | modelo | ✓ | ✓ | ✓ | ✓ |
| Dispositivo da condição | modelo | — | — | ✓ | ✓ |
| Fato e fonte | metadata | — | — | ✓ | ✓ |
| Pendências | — | — | ✓ documentais | ✓ normativas | ✓ agregadas |
| Alertas | — | — | — | ✓ | ✓ |
| Propostas assistidas | — | — | — | ✓ | ✓ |

## 4. Compressões identificadas

### Candidato

Um candidato guarda uma única `FactualTraceability`, embora vários vínculos
possam compartilhar critério/Activity/Exercise. Os demais vínculos continuam
em `EvaluationContext.metadata` e são recuperados pelo estágio documental.

Classificação: informação recuperável, porém candidato não autossuficiente.

### Agregados da avaliação

`facts_used` deduplica por chave e fonte; `normative_devices` deduplica por
documento e referência. As verificações e condições completas permanecem
armazenadas.

Classificação: projeção resumida sem perda do objeto-fonte.

## 5. Conclusão

A cadeia completa é rastreável enquanto o Assessment permanece acompanhado
de `source_evaluation` e o pipeline mantém acesso ao `EvaluationContext`.
Não foi identificada perda irrecuperável.

A garantia não se estende ao transporte isolado de `CriterionCandidate`, pois
esse objeto pode representar apenas a primeira de várias origens factuais.

## 6. Testes recomendados

- duas Evidences e dois Documents para o mesmo candidato;
- duas categorias para o mesmo documento;
- fatos com mesma chave/fonte e valores distintos em condições diferentes;
- serialização e reconstrução completa da cadeia;
- alteração maliciosa de adapter normativo após criação do resultado.
