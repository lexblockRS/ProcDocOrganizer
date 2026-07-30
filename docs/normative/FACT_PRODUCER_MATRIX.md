# Matriz de Produtores de Fatos e Responsabilidades

## 1. Produção, consumo e preservação

| Informação | Produz | Consome | Preserva |
|---|---|---|---|
| projeto e metadata | EvaluationContextBuilder | Candidate e Constraint | EvaluationContext |
| Activities | EvaluationContextBuilder | Candidate | Candidate e cadeia `source_evaluation` |
| FunctionalExercises | EvaluationContextBuilder | Candidate | Candidate e cadeia `source_evaluation` |
| Assignments | EvaluationContextBuilder | Candidate | FactualTraceability por ID |
| Evidences | EvaluationContextBuilder | Candidate | FactualTraceability por ID |
| Documents | EvaluationContextBuilder | Candidate, Qualification e Assessment | Qualification e AssessmentTraceability |
| vínculo critério–fato | produtor externo de metadata | Candidate e Qualification | Candidate/FactualTraceability |
| categoria documental | produtor externo do link e modelo normativo | Candidate e Qualification | Qualification/source_evaluation |
| condições normativas | adaptador normativo | Constraint | Constraint e AssessmentTraceability |
| fatos de condição | produtor externo de metadata | Constraint | `FactUsed` e AssessmentTraceability |
| status consolidado | AssessmentEngine | consumidor futuro | Assessment |
| regra executável | Modelo Executável | nenhum componente atual | nenhum |

## 2. Redundâncias

### Datas e papel

`start_date`, `end_date`, `role`, `organization`, `unit` e
`administrative_reference` existem tanto em FunctionalExercise quanto em
FunctionalAssignmentEvidence. Não há, no contrato auditado, seleção explícita
da fonte canônica para a regra executável.

### Documentos

Document identity aparece em:

- EvaluationDocument;
- EvaluationEvidence;
- `criterion_candidate_links`;
- FactualTraceability;
- PresentedDocument;
- MissingDocument.

A redundância sustenta validação cruzada, mas exige consistência de IDs e
identidades.

### Origem normativa

Origem normativa aparece no Candidate, Qualification, Constraint e Assessment.
Essa repetição é preservação deliberada. O ponto ausente é o ID da regra
executável.

## 3. Nomenclatura

| Modelo Executável | Pipeline | Divergência |
|---|---|---|
| `period_start` | `start_date` | sinônimos |
| `period_end` | `end_date` | sinônimos |
| `role` | `role` | nome igual; vocabulário não alinhado |
| `measurement_unit` | `unit` | nome reduzido no contexto |
| `required_facts` | `constraint_facts` / `FactUsed` | requisito versus ocorrência |
| `accepted_documents` | `accepted_document_id`, `AcceptedDocument` | perfil normativo versus associação concreta |
| `prerequisite_conditions` | `NormativeCondition` | conceito equivalente, contrato separado |
| `article_reference` | `legal_reference` | ID estruturado versus texto |
| `traceability` | `FactualTraceability`, `NormativeOrigin`, `AssessmentTraceability` | um termo para três recortes |
| `computability_level` | nenhum | sem equivalente |
| `counting_rule` | `operation` | não equivalentes; evitar padronização indevida |

## 4. Padronizações futuras recomendadas

Sem implementar nesta Sprint:

- definir aliases formais `period_start ↔ start_date` e
  `period_end ↔ end_date`;
- definir a fonte canônica de papel e período;
- criar contrato tipado para fatos requeridos, em substituição ao schema
  implícito de metadata;
- manter separados `counting_rule` normativo e `operation` de verificação;
- adicionar `execution_rule_id` à rastreabilidade de futura integração;
- distinguir perfil de documentos aceitos de documento efetivamente
  apresentado.

## 5. Fronteira factual

Os Engines auditados não produzem fatos de domínio. Candidate projeta vínculo,
Qualification qualifica documentos, Constraint verifica fatos fornecidos e
Assessment consolida. Essa distribuição está correta.

As lacunas devem ser preenchidas futuramente antes do pipeline ou por um
preparador factual dedicado, nunca por inferência dentro dos Engines atuais.
