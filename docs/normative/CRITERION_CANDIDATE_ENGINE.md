# Criterion Candidate Engine

## 1. Responsabilidade

O `CriterionCandidateEngine` responde exclusivamente:

> Este critério possui um vínculo factual explícito que justifica análise
> posterior?

Um candidato não afirma atendimento, elegibilidade, pontuação, prioridade ou
probabilidade. A saída é uma lista de hipóteses rastreáveis para outro
componente analisar futuramente.

## 2. Fronteira

```text
Modelo Normativo somente leitura ─────┐
                                     │ configuração
                                     ▼
EvaluationContext ──────────► CriterionCandidateEngine
                                      │
                                      ▼
                         CriterionCandidateCollection
```

`generate()` recebe somente `EvaluationContext`. O Modelo Normativo é uma
dependência somente leitura fornecida ao construtor e não é modificado.

O Engine não acessa Repositories, SQLite, Controllers, Workspaces ou Aggregate
Roots.

## 3. Contrato mínimo do Modelo Normativo

O Engine utiliza somente:

- `find_criterion(criterion_id)`;
- `find_requirement(requirement_id)`;
- `find_accepted_document(document_type_id)`.

Os registros normativos precisam expor identidade e origem jurídica. O Engine
não conhece os arquivos JSON nem a estrutura documental que os sustenta.

## 4. Vínculo explícito de entrada

O Builder do contexto pode registrar em `metadata` a coleção imutável
`criterion_candidate_links`. Cada item possui:

| Campo | Obrigatório | Finalidade |
|---|---|---|
| `criterion_id` | sim | critério indicado explicitamente |
| `activity_id` | sim | Activity factual relacionada |
| `functional_exercise_id` | sim | exercício relacionado |
| `functional_assignment_evidence_id` | sim | interpretação intermediária |
| `evidence_id` | sim | Evidence de origem |
| `document_identity` | sim | identidade documental opaca |
| `accepted_document_id` | não | categoria aceita registrada na norma |

O vínculo é informação factual estruturada. O Engine não cria esses dados a
partir de descrição, cargo, trecho documental ou nome de arquivo.

## 5. Algoritmo determinístico

Para cada vínculo, na ordem do metadata:

1. valida todos os campos obrigatórios;
2. localiza o critério no Modelo Normativo;
3. obtém o requisito declarado pelo registro do critério;
4. localiza Activity e FunctionalExercise no contexto;
5. valida a cadeia até FunctionalAssignmentEvidence;
6. valida a referência desta para Evidence;
7. valida a identidade Evidence → Document;
8. quando informada, valida a categoria em documentos aceitos;
9. elimina repetição da mesma combinação
   critério/Activity/FunctionalExercise;
10. cria o candidato e sua justificativa técnica.

Não há tokenização, busca textual, aproximação semântica ou escolha do “melhor”
critério.

## 6. Saída

### `CriterionCandidate`

- `criterion_id`;
- `requirement_id`;
- `normative_origin`;
- `activity`;
- `functional_exercise`;
- `confidence`;
- `technical_justification`;
- `factual_traceability`.

### `NormativeOrigin`

Preserva:

- `document_id`;
- `legal_reference`;
- hierarquia jurídica.

### `FactualTraceability`

Preserva:

- Activity;
- FunctionalExercise;
- FunctionalAssignmentEvidence;
- Evidence;
- ID e identidade do Document;
- categoria documental aceita, quando informada.

### `CriterionCandidateCollection`

É uma coleção imutável, ordenada e sem duplicidades. Ela não calcula totais,
não classifica e não ordena candidatos por mérito.

## 7. Confiança estrutural

`StructuralConfidence` não é probabilidade nem ranking:

- `EXPLICIT_CHAIN`: vínculo explícito e cadeia factual válida;
- `ACCEPTED_DOCUMENT_CHAIN`: além da cadeia explícita, o metadata aponta para
  categoria documental existente no Modelo Normativo.

Os valores descrevem quais verificações estruturais foram realizadas. Não
expressam força probatória.

## 8. Justificativa

A justificativa é construída com mensagens fixas e IDs verificáveis. Ela
registra:

- o vínculo explícito ao critério;
- o requisito obtido do Modelo Normativo;
- a ligação Activity → FunctionalExercise;
- o alcance da cadeia até Evidence e Document;
- a categoria documental aceita, quando disponível.

A justificativa nunca utiliza expressões como “critério satisfeito” ou
“atividade elegível”.

## 9. Invariantes

- o contexto permanece imutável;
- o Modelo Normativo é somente leitura;
- todo critério e requisito deve existir;
- toda relação factual deve coincidir com o snapshot;
- a origem normativa é obrigatória;
- a cadeia factual é preservada integralmente;
- candidatos repetidos não são emitidos;
- a ordem da primeira ocorrência é preservada;
- uma categoria documental desconhecida não gera candidato;
- a execução repetida sobre as mesmas entradas produz resultado igual.

## 10. Limitações

- somente vínculos explicitamente registrados podem gerar candidatos;
- a categoria documental depende de ID normativo já associado no metadata;
- ausência de candidato não significa que o critério não foi atendido;
- presença de candidato não significa que o critério foi atendido;
- o Engine não verifica conteúdo, autenticidade ou suficiência do documento;
- não há tratamento de sobreposição normativa;
- não há pontuação, elegibilidade, decisão ou priorização;
- nenhuma técnica de IA, embedding ou aprendizado de máquina é utilizada.
