# Criterion Assessment Engine

## 1. Responsabilidade

O `CriterionAssessmentEngine` consolida em um único objeto todas as informações
produzidas para um critério candidato:

- candidatura estrutural;
- qualificação documental;
- verificações de condições;
- fatos;
- propostas assistidas;
- pendências;
- alertas;
- lacunas;
- necessidade de revisão humana.

O Assessment descreve o estágio da análise. Ele não declara satisfação do
critério, elegibilidade, pontuação ou decisão administrativa.

## 2. Fronteira

```text
EvaluationContext somente leitura ───────────┐
Modelo Normativo somente leitura ────────────┤ validação
                                             ▼
ConstraintEvaluatedCandidateCollection
                    │
                    ▼
        CriterionAssessmentEngine
                    │
                    ▼
        CriterionAssessmentCollection
```

O Engine não acessa Repositories, SQLite, Controllers, Workspaces ou Aggregate
Roots.

## 3. Composição do Assessment

Cada `CriterionAssessment` contém:

- `criterion_id`;
- `requirement_id`;
- `candidate_status`;
- `documentation_status`;
- `constraint_status`;
- `assessment_status`;
- `human_review_required`;
- `normative_gaps`;
- `warnings`;
- `assisted_proposals`;
- `traceability`;
- `assessment_summary`;
- `source_evaluation`.

`source_evaluation` preserva integralmente o
`ConstraintEvaluatedCandidate`. Assim, a projeção consolidada não substitui
nem descarta nenhum resultado anterior.

## 4. Estados documentais

### `COMPATIBLE`

Existe ao menos um documento associado a categoria oficial e não há documento
ou categoria pendente.

### `PARTIAL`

Existe documentação compatível, mas permanecem documentos ou categorias
pendentes.

### `INSUFFICIENT`

Não existe associação entre documento apresentado e categoria documental
oficial.

Esses estados tratam somente de compatibilidade documental.

## 5. Estados consolidados das condições

| Estado | Significado |
|---|---|
| `COMPLETE` | verificações existentes não apresentam bloqueio conhecido |
| `REVIEW_PENDING` | existe revisão, decisão humana ou condição não verificada |
| `INFORMATION_INCOMPLETE` | alguma verificação carece de informação |
| `NORMATIVE_GAP` | alguma condição possui lacuna normativa |
| `NOT_APPLICABLE` | todas as condições foram explicitamente não aplicáveis |
| `NO_CONDITIONS` | o modelo declarou coleção vazia de condições |

`COMPLETE` não significa critério atendido.

## 6. Estado geral do Assessment

### `READY_FOR_SCORING`

Documentação compatível e ausência de bloqueios conhecidos nas condições.
Significa apenas que o próximo estágio técnico pode consumir o Assessment.

### `REVIEW_REQUIRED`

Existe proposta assistida, decisão humana, condição não verificada ou outra
revisão pendente.

### `NORMATIVE_GAP`

Ao menos uma lacuna normativa está presente.

### `INSUFFICIENT_INFORMATION`

A documentação é parcial/insuficiente ou faltam fatos para verificar
condições.

### `NOT_APPLICABLE`

Todas as condições identificadas foram explicitamente marcadas como não
aplicáveis.

Nenhum desses estados equivale a aprovação ou rejeição.

## 7. Regras de precedência

A consolidação utiliza a seguinte ordem:

1. `NORMATIVE_GAP`;
2. `INSUFFICIENT_INFORMATION`;
3. `REVIEW_REQUIRED`;
4. `NOT_APPLICABLE`;
5. `READY_FOR_SCORING`.

Essa precedência impede que uma lacuna ou ausência factual seja ocultada por
uma verificação favorável.

## 8. Explicabilidade

`AssessmentTraceability` preserva:

- origem normativa;
- cadeia factual;
- documentos apresentados;
- condições;
- verificações;
- fatos utilizados.

`warnings` agrega, sem duplicidade:

- alertas das verificações;
- documentos ausentes;
- categorias pendentes.

`assessment_summary` informa os três estados consolidados e as quantidades de
verificações, fatos, pendências e alertas. O resumo declara expressamente que
o estágio não representa aprovação nem satisfação.

## 9. Invariantes

- Assessment e coleção são imutáveis;
- a ordem de entrada é preservada;
- resultados duplicados são rejeitados;
- candidato, qualificação e avaliação anteriores permanecem acessíveis;
- propostas assistidas mantêm `definitive = false`;
- documentos apresentados devem pertencer ao `EvaluationContext`;
- critério e requisito devem existir no Modelo Normativo;
- lacunas e alertas não são descartados;
- as mesmas entradas produzem o mesmo resultado.

## 10. Relação com o futuro Scoring Engine

`READY_FOR_SCORING` define somente uma fronteira técnica. Um futuro componente
de pontuação poderá receber Assessments nesse estágio, mas deverá:

- consultar exclusivamente valores normativos oficiais;
- preservar a rastreabilidade;
- não reinterpretar verificações anteriores;
- recusar ou tornar visíveis lacunas e revisões pendentes;
- manter pontuação separada de elegibilidade e decisão final.

Nenhum cálculo ou contrato de pontuação é implementado nesta Sprint.

## 11. Limitações

- a consolidação não reexecuta verificações;
- não resolve conflitos entre condições;
- não decide se alertas são superáveis;
- não interpreta documentos ou texto normativo;
- não calcula pontuação;
- não define elegibilidade;
- não produz resultado final ou decisão definitiva.
