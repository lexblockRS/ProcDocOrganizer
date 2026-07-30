# Matriz de Cobertura de Campos

## 1. Classificações

- `FULLY_PRODUCED`: produzido estruturalmente e preservado até o Assessment.
- `PARTIALLY_PRODUCED`: existe informação equivalente ou opcional, sem contrato
  completo.
- `NOT_PRODUCED`: nenhum componente do pipeline produz o campo.
- `DERIVED_FROM_NORM`: pertence à norma ou regra, não ao domínio factual.

## 2. Campos da regra executável

| Campo | Cobertura | Produtor/origem | Etapa | Chega ao Assessment? |
|---|---|---|---|---|
| `criterion_id` | `FULLY_PRODUCED` | CandidateEngine, após consulta normativa | Candidate | sim, campo direto |
| `requirement_id` | `FULLY_PRODUCED` | CandidateEngine, após consulta normativa | Candidate | sim, campo direto |
| `article_reference` | `PARTIALLY_PRODUCED` | `NormativeOrigin.legal_reference/hierarchy` | Candidate | sim, mas não como ID do artigo |
| `annex_reference` | `PARTIALLY_PRODUCED` | `NormativeOrigin.hierarchy` | Candidate | sim, apenas dentro da hierarquia |
| `scoring_table` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `measurement_type` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `measurement_unit` | `PARTIALLY_PRODUCED` | `FunctionalExercise.unit` e Assignment `unit` | Context | sim via objetos-fonte, sem vínculo com a unidade normativa |
| `counting_rule` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `temporal_rule` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `variant_rule` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `aggregation_rule` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `overlap_rule` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `required_facts` | `PARTIALLY_PRODUCED` | Context e `constraint_facts` | Context/Constraint | somente os fatos efetivamente utilizados |
| `accepted_documents` | `PARTIALLY_PRODUCED` | link explícito e Qualification | Candidate/Qualification | categorias usadas, não o perfil normativo completo |
| `prerequisite_conditions` | `PARTIALLY_PRODUCED` | adaptador de condições normativas | Constraint | sim quando o adaptador as fornece |
| `computability_level` | `DERIVED_FROM_NORM` | Modelo Executável | fora do pipeline | não |
| `traceability` | `PARTIALLY_PRODUCED` | todos os estágios | ponta a ponta | fatos e norma sim; `rule_id` e tabela não |

## 3. Campos do manifesto

| Campo | Cobertura | Observação |
|---|---|---|
| `criterion_id` | `FULLY_PRODUCED` | preservado diretamente |
| `rule_id` | `NOT_PRODUCED` | não existe no pipeline |
| `article_id` | `PARTIALLY_PRODUCED` | referência textual/hierarquia, não ID |
| `requirement_id` | `FULLY_PRODUCED` | preservado diretamente |
| `annex` | `PARTIALLY_PRODUCED` | recuperável da hierarquia |
| `table_id` | `NOT_PRODUCED` | não é consultado nem preservado |
| `accepted_documents_profile` | `NOT_PRODUCED` | apenas categorias selecionadas aparecem |

## 4. Fatos exigidos

| Fato | Cobertura | Produtor existente | Preservação |
|---|---|---|---|
| `period_start` | `PARTIALLY_PRODUCED` | Exercise `start_date`; Assignment `start_date` opcional | objetos no source; vira `FactUsed` apenas via metadata |
| `period_end` | `PARTIALLY_PRODUCED` | Exercise/Assignment `end_date`, ambos opcionais | objetos no source; vira `FactUsed` apenas via metadata |
| `role` | `PARTIALLY_PRODUCED` | Exercise e Assignment | preservado no source; vocabulário titular/substituto não validado |
| `designation_count` | `NOT_PRODUCED` | nenhum | não |
| `project_count` | `NOT_PRODUCED` | nenhum | não |
| `product_count` | `NOT_PRODUCED` | nenhum | não |
| `mandate_count` | `NOT_PRODUCED` | nenhum | não |
| `event_count` | `NOT_PRODUCED` | nenhum | não |
| `training_count` | `NOT_PRODUCED` | nenhum | não |
| `award_count` | `NOT_PRODUCED` | nenhum | não |
| `system_count` | `NOT_PRODUCED` | nenhum | não |
| `patent_count` | `NOT_PRODUCED` | nenhum | não |
| `course_count` | `NOT_PRODUCED` | nenhum | não |
| `research_group_count` | `NOT_PRODUCED` | nenhum | não |
| `publication_count` | `NOT_PRODUCED` | nenhum | não |

Qualquer um desses valores pode ser transportado genericamente por
`constraint_facts`, mas metadata é um canal de entrada, não um produtor.

## 5. Cobertura consolidada

Dos 17 campos de cada regra:

- 2 são plenamente produzidos;
- 7 são parcialmente produzidos;
- 8 pertencem ao Modelo Executável e não são materializados no pipeline.

No manifesto, `rule_id`, `table_id` e o perfil documental não chegam ao
Assessment.
