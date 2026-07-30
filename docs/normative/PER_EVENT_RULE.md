# Regra PER_EVENT

## Definição

`PER_EVENT` representa pontuação por ocorrência individual
normativamente reconhecida. Na infraestrutura atual, a quantidade factual é
fornecida exclusivamente por `Measurement.amount`; o Kernel não conta,
deduplica, cria ou infere ocorrências.

## Compatibilidade

A etapa `ExecutionCompatibility`, anterior ao contrato e ao Kernel, exige uma
medição quantitativa compatível com a declaração da regra. `DURATION` é
incompatível com `PER_EVENT`.

`ExecutionValidation` verifica somente completude e consistência factual. O
Kernel não repete a verificação de compatibilidade.

## Fórmula

```text
quantity = Decimal(Measurement.amount)
score = quantity × resolved_normative_value.value
```

Zero é quantidade válida. Inteiros são normalizados diretamente para
`Decimal`; valores `Decimal` são preservados. `float` não é aceito e nenhuma
conversão automática de unidade é realizada.

## Bloqueios

O cálculo não ocorre quando o contrato chega como não executável ou bloqueado,
inclusive por:

- validação factual bloqueada;
- `Measurement` incompatível;
- quantidade ausente;
- valor normativo ausente;
- regra declarativa incompatível.

O Kernel sempre produz um `CriterionScore`; nunca retorna `None`.

## Rastreabilidade e explicabilidade

O Score preserva contrato, fato, validação, origem da Measurement e
rastreabilidade do valor normativo. A explicação registra:

- regra `PER_EVENT`;
- tipo e unidade da Measurement;
- quantidade de eventos;
- valor normativo por evento;
- multiplicação executada;
- resultado ou motivo de bloqueio.

## Invariantes

1. `PER_EVENT` nunca interpreta datas.
2. `PER_EVENT` nunca interpreta `Measurement DURATION`.
3. `PER_EVENT` nunca cria ocorrências.
4. A quantidade provém exclusivamente da Measurement factual já existente.
5. O cálculo utiliza somente aritmética `Decimal`.
