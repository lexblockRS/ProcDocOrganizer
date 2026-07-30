# Vocabulário Canônico de Fatos

## 1. Finalidade

O vocabulário torna explícitos os aliases entre domínio factual, Assessment e
execução normativa. Nenhum sinônimo é aceito implicitamente.

A fonte computável é `canonical_fact_vocabulary.json`.

## 2. Normalizações

| Origem | Nome canônico | Transformação | Reversão |
|---|---|---|---|
| `EvaluationFunctionalExercise.start_date` | `period_start` | renomeação | `source_field = start_date` |
| `EvaluationFunctionalExercise.end_date` | `period_end` | renomeação | `source_field = end_date` |
| `EvaluationFunctionalExercise.role` | `execution_role` | renomeação | `source_field = role` |
| `ExecutionRule.measurement_unit` | `measurement_unit` | declaração normativa | `rule_id` e tabela |

Datas não são convertidas. Papel não é traduzido. Unidade factual não substitui
a unidade normativa.

## 3. Contagens

As contagens reconhecidas são:

- `designation_count`;
- `project_count`;
- `product_count`;
- `mandate_count`;
- `event_count`;
- `training_count`;
- `award_count`;
- `system_count`;
- `patent_count`;
- `course_count`;
- `research_group_count`;
- `publication_count`.

Elas somente são criadas quando `AssessmentTraceability.facts` possui exatamente
a chave requerida. O Builder não conta objetos, documentos ou Activities.

## 4. Reversibilidade

Todo CanonicalFact inclui `FactTraceability`, com:

- tipo do objeto-fonte;
- nome original do campo;
- identidade da fonte;
- referência normativa, quando aplicável.

Assim, `period_start` nunca perde o nome `start_date`, e
`measurement_unit` nunca perde a regra que a declarou.

## 5. Fatos genéricos

Um fato de Constraint que não pertence ao vocabulário fechado pode ser
preservado como `CONSTRAINT_FACT`, mas não satisfaz silenciosamente um fato
canônico requerido. Essa decisão evita sinônimos implícitos.

## 6. Evolução

Novos aliases exigem alteração explícita e versionada do JSON, documentação e
testes. O Builder não cria aliases por heurística.
