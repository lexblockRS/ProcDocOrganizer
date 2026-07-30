# Scoring Arithmetic

## Normalização

Para medições quantitativas, a quantidade de entrada é copiada de
`contract.measurement.amount`. Valores inteiros são convertidos
diretamente para `Decimal`; valores já decimais são preservados. Zero é
um operando válido. Booleanos, `float` e outros tipos não são aceitos.

Em medições `DURATION`, `measurement.amount` permanece ausente. A
quantidade normativa é derivada posteriormente do intervalo temporal
canônico pela regra executada no Kernel.

O valor unitário é lido exclusivamente de
`contract.resolved_normative_value.value` e deve chegar como `Decimal`.
O Kernel não pesquisa, converte nem escolhe valores normativos.

## Operação

Para `PER_EVENT` e `PER_PUBLICATION`:

`calculated_score = normalized_quantity × normative_operand`

Para `PER_YEAR` com regra temporal de anos completos, a quantidade é
derivada exclusivamente do intervalo canônico presente no contrato:

`calculated_score = Decimal(anos completos) × normative_operand`

Anos incompletos são descartados, sem arredondamento. Intervalos menores
que um ano resultam em zero. Períodos abertos, datas inválidas ou
invertidas, múltiplas ocorrências e sobreposições ficam bloqueados.

Para `FRACTION_ABOVE_SIX_MONTHS`, a mesma decomposição calcula primeiro
os anos completos e depois compara o resíduo ao marco de seis
meses-calendário:

`anos considerados = anos completos + (1 se fração residual ≥ 6 meses)`

Exatamente seis meses produzem incremento `+1`. Resíduos inferiores
produzem incremento `+0`.
Meses são meses-calendário completos após o último aniversário; dias
residuais são a diferença posterior ao último mês completo. Datas em
29 de fevereiro usam 28 de fevereiro como aniversário em anos não
bissextos.

Para `PER_MONTH`, a quantidade é o total canônico de meses-calendário
completos:

`calculated_score = Decimal(completed_months) × normative_operand`

`completed_months` pertence à decomposição temporal canônica e equivale
a `complete_years × 12 + residual_months`. O Kernel consome a propriedade
pronta; não recompõe esse valor.

Dias residuais são preservados para explicabilidade, mas nunca produzem
mês adicional. `PER_MONTH` não usa aproximações por quantidade fixa de
dias, não produz fração decimal e não aplica
`FRACTION_ABOVE_SIX_MONTHS`.

Não há outra conversão temporal, teto, mínimo, máximo ou transformação.
A aritmética `Decimal` evita a perda de precisão binária.

## Princípio arquitetural temporal

Toda regra temporal do sistema deve consumir uma decomposição temporal
canônica. Nenhuma regra normativa implementa algoritmos próprios de
manipulação de datas.

`PER_YEAR`, `FRACTION_ABOVE_SIX_MONTHS` e `PER_MONTH` pertencem a essa
mesma família e consomem a decomposição existente, sem duplicar cálculo
de datas.

Os `TemporalAttention` também consomem essa decomposição, mas pertencem
exclusivamente à interface de revisão. Eles são produzidos depois do
Score e não alteram cálculo, estado, contrato ou resultado normativo.

## Princípio da neutralidade factual

`ExecutionFact` representa exclusivamente fatos observáveis.
`Measurement` representa exclusivamente a informação originalmente
disponível.

Valores derivados de interpretação normativa não podem ser
materializados antecipadamente em `ExecutionFact` nem em `Measurement`.
Transformações como anos considerados, meses completos, dias computáveis
e quantidade normativa pertencem exclusivamente ao
`CriterionScoringKernel` ou à infraestrutura temporal canônica por ele
utilizada.

As etapas anteriores apenas verificam se existem fatos suficientes para
permitir a execução normativa. Elas não antecipam a transformação do
intervalo em quantidade.

## Rastreabilidade

O trace registra o contrato, o fato de execução, a validação, a origem
da medição, a rastreabilidade do valor normativo e a fórmula aplicada.
Quando o cálculo não ocorre, o Score conserva os operandos disponíveis
e explica o motivo do bloqueio ou da não execução.
