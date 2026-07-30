# Scoring Arithmetic

## Normalização

A quantidade de entrada é copiada de `contract.measurement.amount`.
Valores inteiros são convertidos diretamente para `Decimal`; valores
já decimais são preservados. Zero é um operando válido. `None` permanece
ausente. Booleanos, `float` e outros tipos não são aceitos.

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

Não há outra conversão temporal, teto, mínimo, máximo ou transformação.
A aritmética `Decimal` evita a perda de precisão binária.

## Princípio arquitetural temporal

Toda regra temporal do sistema deve consumir uma decomposição temporal
canônica. Nenhuma regra normativa implementa algoritmos próprios de
manipulação de datas.

`PER_YEAR`, `FRACTION_ABOVE_SIX_MONTHS` e `PER_MONTH` pertencem a essa
mesma família. `PER_MONTH` ainda não possui execução nesta versão; sua
implementação futura deverá consumir a decomposição existente, sem
duplicar cálculo de datas.

Os `TemporalAttention` também consomem essa decomposição, mas pertencem
exclusivamente à interface de revisão. Eles são produzidos depois do
Score e não alteram cálculo, estado, contrato ou resultado normativo.

## Rastreabilidade

O trace registra o contrato, o fato de execução, a validação, a origem
da medição, a rastreabilidade do valor normativo e a fórmula aplicada.
Quando o cálculo não ocorre, o Score conserva os operandos disponíveis
e explica o motivo do bloqueio ou da não execução.
