# PER_YEAR Rule

## Escopo

O `CriterionScoringKernel` suporta `PER_YEAR` somente quando o
`CriterionExecutionContract` descreve anos completos. São aceitas as
regras temporais declarativas `NONE`, `FULL_YEARS`, `COMPLETE_YEARS` e
`WHOLE_YEARS`.

`FRACTION_ABOVE_SIX_MONTHS` reutiliza a mesma decomposição temporal e
aplica posteriormente sua própria política. Qualquer outra regra que
exija tratamento temporal permanece bloqueada.

## Pré-condições

O contrato deve fornecer:

- `execution_computability = EXECUTABLE`;
- exatamente uma ocorrência;
- data inicial e final ISO válidas;
- período fechado;
- fim igual ou posterior ao início;
- `overlap_status = NONE`;
- valor normativo resolvido em `Decimal`.

Ausência de datas, período aberto, datas invertidas, sobreposição,
interseção ou múltiplas ocorrências produzem `BLOCKED`, sem resultado.
Estados textuais ou de revisão humana explicitamente recebidos pelo
contrato são preservados e também não calculam.

## Anos completos

Os anos são contados por aniversários completos entre início e fim.
Uma parcela incompleta é descartada, nunca arredondada. Um intervalo
menor que um ano produz quantidade zero e pode ser executado.

Para início em 29 de fevereiro, 28 de fevereiro é o aniversário nos
anos não bissextos.

A decomposição temporal canônica também informa meses e dias residuais,
mas `PER_YEAR` utiliza exclusivamente os anos completos. A introdução da
política fracionária não altera seu algoritmo nem seu resultado.

`PER_YEAR`, `FRACTION_ABOVE_SIX_MONTHS` e o futuro executor de
`PER_MONTH` consomem obrigatoriamente essa mesma decomposição. Nenhuma
regra normativa implementa algoritmo próprio de manipulação de datas.

## Cálculo

`score = Decimal(anos completos) × valor normativo Decimal`

Não há, dentro de `PER_YEAR`, arredondamento de fração, cálculo mensal,
interseção, sobreposição, elegibilidade ou ranking.

## Explicabilidade

O Score registra na explicação a data inicial, a data final, os anos
completos, o valor normativo, a fórmula e o resultado. O trace continua
preservando contrato, fato, validação e origem normativa do operando.
