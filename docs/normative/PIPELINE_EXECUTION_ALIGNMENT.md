# Alinhamento entre Pipeline e Modelo Normativo Executável

## 1. Escopo

Esta auditoria cruza:

- `criterion_execution_rules.json`;
- `execution_rules_manifest.json`;
- `EvaluationContext`;
- `CriterionCandidate`;
- `EvidenceQualification`;
- `ConstraintEvaluation`;
- `CriterionAssessment`.

Nenhum componente foi alterado. A análise descreve o comportamento existente e
não propõe que o pipeline calcule pontuação.

## 2. Resultado geral

O pipeline está alinhado com a preservação da cadeia factual e com a consolidação
de análises documentais e condicionais. Ele não está integrado ao Modelo
Normativo Executável.

```text
Modelo Executável ── regra_id, medição, contagem, tempo, variante ──┐
                                                                  │ ligação ausente
EvaluationContext ── fatos e vínculos explícitos ── Pipeline ── Assessment
```

Os dois lados compartilham `criterion_id`, `requirement_id`, referências
normativas e categorias documentais, mas não existe objeto ou referência que
associe uma `CriterionExecutionRule` a um candidato ou Assessment.

## 3. Fluxo factual preservado

O `EvaluationContext` fornece:

- Activity;
- FunctionalExercise;
- FunctionalAssignmentEvidence;
- Evidence;
- Document;
- metadata imutável.

O `CriterionCandidate` resolve e registra a cadeia factual completa. A
qualificação acrescenta documentos apresentados, aceitos, ausentes e categorias.
A avaliação de condições acrescenta condições, verificações e fatos utilizados.
O Assessment conserva esses elementos em `AssessmentTraceability` e também
preserva o objeto anterior em `source_evaluation`.

Essa cadeia está funcionalmente preservada:

```text
Document
↑
Evidence
↑
FunctionalAssignmentEvidence
↑
FunctionalExercise
↑
Activity
↓
CriterionCandidate
↓
QualifiedCriterionCandidate
↓
ConstraintEvaluatedCandidate
↓
CriterionAssessment
```

## 4. Fluxo normativo

O pipeline preserva:

- `criterion_id`;
- `requirement_id`;
- `NormativeOrigin.document_id`;
- `legal_reference`;
- `hierarchy`;
- categorias documentais e suas referências;
- condições normativas fornecidas pelo adaptador;
- dispositivos associados às condições.

O pipeline não preserva explicitamente:

- `rule_id`;
- referência ao manifesto;
- tabela de pontuação;
- tipo e unidade de medição como regra;
- counting rule;
- temporal rule;
- variant rule;
- aggregation rule;
- overlap rule;
- computability level.

Logo, a cadeia “Norma → Regra Executável → Fato → Assessment” não está fechada.
A cadeia atual é “Norma consultada → candidato/fato → Assessment”.

## 5. Produtores e fronteiras

`EvaluationContextBuilder` é o único produtor factual estrutural. Os Engines
posteriores devem consumir, validar, qualificar e preservar fatos; não devem
inventá-los.

`criterion_candidate_links` e `constraint_facts` são entradas externas guardadas
em metadata. Os Engines não produzem seus fatos de negócio: apenas os leem,
validam e projetam.

Isso preserva corretamente a fronteira arquitetural, mas significa que não há
produtor tipado para vários fatos exigidos pelo Modelo Executável.

## 6. Responsabilidades

| Componente | Produz | Consome | Preserva |
|---|---|---|---|
| EvaluationContext | snapshot factual | Aggregate Roots e repositories, via Builder | identidades, relações, ordem e metadata |
| Candidate | candidato estrutural | vínculos explícitos, contexto e norma | cadeia factual e origem normativa |
| Qualification | resultado documental | candidato, contexto e categorias oficiais | candidato e origem normativa |
| Constraint | verificações | candidato qualificado, condições e metadata factual | qualificação, fatos, condições e dispositivos |
| Assessment | consolidação | resultado de constraints, contexto e norma | todas as etapas via traceability e source |

Nenhum Engine observado cria fatos pertencentes ao domínio factual.

## 7. Conclusão

O pipeline fornece uma base factual rastreável, mas ainda não fornece todas as
entradas declaradas pelo Modelo Executável. Um futuro componente de preparação
de fatos, fora dos Engines auditados, precisará produzir fatos tipados e ligar
explicitamente `rule_id` ao fluxo. Esta é uma recomendação arquitetural, não uma
implementação.
