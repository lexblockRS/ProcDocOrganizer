# ResolvedNormativeValue

## 1. Objetivo

`ResolvedNormativeValue` transporta o operando normativo oficial necessário a
uma futura execução. Ele não multiplica, soma, arredonda ou aplica o valor.

## 2. Campos

- `value`: Decimal normalizado ou `None`;
- `unit`: unidade oficial do critério;
- `table_id`: tabela normativa;
- `criterion_id`: critério de origem;
- `legal_basis`: referência jurídica já presente no dataset;
- `traceability`: origem completa.

## 3. Normalização

Os valores de `decree_criteria.json` usam vírgula decimal. O Resolver converte,
por exemplo, `"4,5"` em `Decimal("4.5")`.

Essa transformação apenas oferece representação numérica exata. Nenhuma
operação entre valores é realizada.

## 4. Valores dependentes de variante

Quando `points` é `null` e os valores estão nas variantes, `value` permanece
`None`. Os valores das variantes são preservados em
`traceability.variant_values`, mas nenhuma opção é selecionada.

Nessa situação, `execution_computability` é `NOT_EXECUTABLE`.

## 5. Rastreabilidade

`NormativeValueTraceability` conserva:

```text
BR-DEC-13048-2026
    ↓
decree_criteria.json
    ↓
tabela
    ↓
critério
    ↓
campo points ou variants
    ↓
valor original
    ↓
ResolvedNormativeValue
```

Também permanecem anexo, item e referência jurídica.

## 6. Falhas

São rejeitados:

- critério inexistente;
- tabela divergente;
- valor não textual ou decimal inválido;
- identidade normativa incompatível.
