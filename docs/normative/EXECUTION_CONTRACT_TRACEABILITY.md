# Rastreabilidade do Contrato de Execução

## 1. Cadeia

```text
Decreto estruturado
    ↓
CriterionExecutionRule
    ↓
Manifest entry
    ↓
ExecutionFact
    ↓
ExecutionValidation
    ↓
CriterionExecutionContract
```

## 2. Identidades normativas

O contrato preserva:

- `execution_rule_id`;
- `criterion_id`;
- `requirement_id`;
- `article_reference`;
- `annex_reference`;
- `applicable_table`;
- documentos aceitos;
- fatos requeridos;
- `ExecutionNormativeTraceability`.

Não é introduzido `legal_reference` textual. O texto oficial permanece na
camada documental.

## 3. Identidades factuais

O contrato preserva diretamente:

- `execution_fact_id`;
- Measurement;
- Occurrences;
- CanonicalFacts;
- CanonicalDocuments;
- FactualTraceability;
- ExecutionFact completo.

Nenhum objeto factual é copiado para estrutura mutável.

## 4. Identidades de validação

O contrato preserva:

- `validation_id`;
- `validation_state`;
- itens não resolvidos;
- `ExecutionValidationTraceability`;
- ExecutionValidation completa.

Assim, cada estado pode ser explicado pela Validation que o produziu.

## 5. Correspondência

Antes da montagem são comparados:

- Fact `execution_fact_id` ↔ Validation `execution_fact_id`;
- Fact `execution_rule_id` ↔ Validation e regra;
- Fact `criterion_id` ↔ Validation, regra e manifesto;
- Fact `requirement_id` ↔ regra e manifesto;
- tabela da regra ↔ tabela do manifesto.

Essas comparações confirmam identidade de montagem; elas não repetem a validação
factual.

## 6. Determinismo

`contract_id` é UUID v5 derivado dos IDs de Fact, Validation e regra. A mesma
entrada produz o mesmo contrato e a mesma ordem.
