# Modelo ExecutionFact

## 1. Objetivo

`ExecutionFact` é o contrato factual imutável entre o pipeline de Assessment e
uma futura camada de aplicação normativa. Ele não calcula pontos, não decide
elegibilidade e não executa regras.

```text
CriterionAssessmentCollection
        +
EvaluationContext
        +
Modelo Executável
        ↓
ExecutionFactBuilder
        ↓
ExecutionFactCollection
```

## 2. Modelos

### ExecutionFact

Reúne:

- identidades do fato, critério, requisito e regra;
- estado do Assessment e computabilidade declarada;
- Measurement;
- ocorrências preservadas;
- fatos, documentos, Activities e FunctionalExercises canônicos;
- intervalo temporal;
- variantes possíveis, sem variante selecionada;
- candidatos a sobreposição;
- pendências e necessidade de revisão;
- rastreabilidade normativa e factual;
- explicação;
- Assessment de origem.

### CanonicalFact

Cada fato possui identidade determinística, tipo fechado, valor imutável, unidade,
fonte, origem estrutural da confiança e rastreabilidade reversível.

`ConfidenceOrigin` possui:

- `EXPLICIT`: presente diretamente no snapshot ou Assessment;
- `DERIVED`: produzido por transformação estrutural declarada;
- `DECLARED`: proveniente do Modelo Executável.

Esses valores não representam probabilidade.

### Measurement

Contém `amount`, `unit`, `measurement_type`, `source` e `validation_state`.
O Builder apenas transporta uma quantidade explicitamente disponível. Ele não
multiplica a quantidade pelo valor da tabela.

Estados:

- `AVAILABLE`;
- `MISSING`;
- `REVIEW_REQUIRED`.

### ExecutionOccurrence

Representa uma origem factual sem soma ou eliminação. Preserva quantidade,
unidade, período, documentos, Activity, FunctionalExercise, estado de
sobreposição e explicação.

## 3. Identidade

IDs de ExecutionFact, Occurrence e CanonicalFact são UUIDs v5 determinísticos,
gerados a partir de identidades já existentes. Repetir a construção com a mesma
entrada produz os mesmos IDs e a mesma ordem.

## 4. Imutabilidade

Todos os modelos são dataclasses `frozen` e `slots`. Coleções internas usam
tuplas. Valores canônicos aceitam somente string, inteiro, booleano ou Decimal.
O Assessment é preservado como objeto imutável de origem.

## 5. Variantes

O Builder transporta:

- opções declaradas;
- disponibilidade do fato `role`;
- necessidade de revisão;
- `selected_variant = None`.

Mesmo quando o papel factual coincide textualmente com uma variante, nenhuma
seleção ocorre.

## 6. Sobreposição

Quando dois Assessments compartilham Activity, FunctionalExercise e
FunctionalAssignmentEvidence, seus fatos são registrados como candidatos
estruturais e recebem `POSSIBLE`. Sem candidato, o estado é `NONE`.

`CONFIRMED` e `UNKNOWN` pertencem ao vocabulário, mas o Builder não confirma nem
resolve sobreposições.

## 7. Limitações

- cada Assessment origina uma ocorrência estrutural;
- múltiplas quantidades somente existem se vierem explicitamente nos fatos;
- não há conversão ou cálculo de duração;
- não há seleção de variante;
- não há soma, deduplicação normativa ou aplicação de tabela;
- condições textuais continuam dependentes de revisão.
