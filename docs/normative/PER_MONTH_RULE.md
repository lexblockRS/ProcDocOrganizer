# PER_MONTH Rule

## Definição normativa

`PER_MONTH` atribui uma unidade normativa para cada mês-calendário
completo do intervalo factual:

`quantity = completed_months`

`score = Decimal(completed_months) × normative_value`

Dias residuais não produzem mês adicional, não são convertidos em
fração decimal e não sofrem arredondamento.

## Mês-calendário completo

Um mês completa-se quando a data final alcança o marco mensal derivado
da data inicial. Quando o mês de destino não possui o dia original, o
marco utiliza seu último dia válido.

Exemplos:

| Início | Fim | Meses completos |
| --- | --- | ---: |
| 01/01/2020 | 31/01/2020 | 0 |
| 01/01/2020 | 01/02/2020 | 1 |
| 15/01/2020 | 14/02/2020 | 0 |
| 15/01/2020 | 15/02/2020 | 1 |
| 15/01/2020 | 16/02/2020 | 1 |
| 31/01/2020 | 29/02/2020 | 1 |
| 29/02/2020 | 28/02/2021 | 12 |

Não existe aproximação por trinta dias.

## Fonte temporal canônica

`PER_MONTH` não manipula datas. Ele consome
`TemporalDecomposition.completed_months`, propriedade pública e imutável
da decomposição temporal compartilhada com `PER_YEAR` e
`FRACTION_ABOVE_SIX_MONTHS`.

A propriedade satisfaz:

`completed_months = complete_years × 12 + residual_months`

Essa relação é implementada exclusivamente na infraestrutura temporal.
O Kernel não a recalcula.

## Computabilidade e neutralidade factual

Uma medição `DURATION` é computável quando possui intervalo canônico
completo e válido. `measurement.amount` permanece `None`: nenhuma etapa
anterior materializa meses, anos, dias computáveis ou quantidade
normativa.

O Kernel é a primeira etapa que transforma o intervalo em quantidade
normativa.

## Casos bloqueados

- contrato cuja `execution_computability` não seja `EXECUTABLE`;
- data inicial ou final ausente;
- período aberto;
- data inválida;
- data final anterior à inicial;
- múltiplas ocorrências sem regra de consolidação;
- sobreposição ou interseção;
- regra temporal incompatível com `PER_MONTH`;
- valor normativo ausente.

O Kernel não corrige nem infere datas.

## Rastreabilidade e explicabilidade

O `CriterionScore` preserva o contrato imutável e, por ele, o
`ExecutionFact`, a `ExecutionValidation`, as ocorrências, a unidade e a
rastreabilidade normativa.

A explicação registra:

- início e fim;
- anos completos;
- meses e dias residuais;
- total canônico de meses completos;
- regra `PER_MONTH`;
- valor e unidade normativa;
- fórmula e resultado.

Para 15/03/2021 a 20/09/2022, com dois pontos por mês:

- decomposição: 1 ano, 6 meses e 5 dias;
- `completed_months`: 18;
- fórmula: `18 × 2`;
- resultado: `36`.

## Relação com outras regras

`PER_YEAR` continua usando somente `complete_years`.
`FRACTION_ABOVE_SIX_MONTHS` continua aplicando exclusivamente sua
política anual de conversão. `PER_MONTH` nunca consulta nem aplica essa
política.

Temporal Attention Flags permanecem posteriores, independentes e sem
efeito sobre o resultado.

## Invariantes

1. Nenhuma aproximação fixa de dias representa um mês.
2. Dias residuais nunca constituem mês completo.
3. A política `FRACTION_ABOVE_SIX_MONTHS` não é aplicada.
4. A única fonte de quantidade é `completed_months`.
5. O Kernel não implementa manipulação calendárica.
6. Attention Flags não alteram cálculo.
7. Não há `float`, mutação, consolidação ou agregação de ocorrências.

