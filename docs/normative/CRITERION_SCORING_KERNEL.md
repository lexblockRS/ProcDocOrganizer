# Criterion Scoring Kernel

## Objetivo

O `CriterionScoringKernel` é o primeiro núcleo matemático oficial do
ProcDocOrganizer. Ele recebe exclusivamente uma
`CriterionExecutionContractCollection` e produz exatamente um
`CriterionScore` para cada contrato, preservando a ordem de entrada.

O Kernel não consulta norma, banco, repositório, Aggregate Root ou etapa
anterior do pipeline. O contrato já contém todos os fatos e operandos
necessários.

## Recorte executável

Somente `PER_EVENT` e `PER_PUBLICATION` são suportadas. Em ambas, a única
operação é:

`pontuação = quantidade normalizada × valor normativo resolvido`

A computabilidade jurídica não é reinterpretada. O Kernel observa
somente `execution_computability`: se ela não for `EXECUTABLE`, produz um
Score `BLOCKED` sem cálculo.

Regras diferentes das duas suportadas produzem `NOT_EXECUTED`. Quantidade
ou valor ausente também impedem a execução. Nenhum caminho retorna
`None` no lugar de um Score.

## Limites

Não há agregação entre critérios ou requisitos, resolução de variantes,
tratamento de sobreposição, interpretação textual, elegibilidade,
ranking ou pontuação global. `PER_YEAR`, `PER_MONTH`, `ROLE_BASED`,
`CUSTOM_TEXT` e `FRACTION_ABOVE_SIX_MONTHS` permanecem fora do Kernel.
