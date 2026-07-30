# FRACTION_ABOVE_SIX_MONTHS Rule

## Política oficial de contagem temporal

Esta política complementa `PER_YEAR`; ela não substitui nem modifica a
contagem de anos completos.

Após a determinação dos anos completos, qualquer período residual igual
ou superior a seis meses-calendário completos acrescenta exatamente um
ano ao total de anos considerados, inclusive quando não existir nenhum
ano completo.

Essa é uma decisão normativa consolidada do sistema e constitui uma
política oficial de conversão de tempo em anos computáveis.

Quando a fração residual é **igual ou superior a seis meses
(≥ 6 meses)**:

`anos considerados = anos completos + 1`

Quando o resíduo é inferior a seis meses:

`anos considerados = anos completos`

Exatamente seis meses já produzem a conversão em um ano considerado.
Não existe conversão proporcional.

## Invariante

`FRACTION_ABOVE_SIX_MONTHS` nunca acrescenta mais de um ano. O incremento
permitido é exclusivamente `+0` ou `+1`; nenhum incremento superior é
válido.

## Decomposição temporal centralizada

A mesma decomposição imutável é o fundamento único de `PER_YEAR`,
`PER_MONTH` e `FRACTION_ABOVE_SIX_MONTHS`. Nenhuma dessas regras
implementa algoritmo próprio de cálculo de datas. `PER_MONTH` ainda não
possui execução nesta versão, mas seu contrato arquitetural exige o
consumo dessa mesma decomposição.

Ela contém:

- data inicial e final;
- anos completos;
- meses residuais completos;
- dias residuais;
- indicador `fraction_at_least_six_months`.

`PER_YEAR` usa somente `complete_years`. A política fracionária usa os
anos e o indicador.

## Definições de calendário

Anos completos são contados por aniversários. Após o último aniversário,
meses residuais são contados como meses-calendário completos. O dia é
limitado ao último dia do mês de destino quando o mês não possui o dia
original. Dias posteriores ao último mês completo formam
`residual_days`.

O indicador é obtido comparando a data final com o marco de seis
meses-calendário após o último aniversário:

- data final anterior ao marco: incremento `+0`;
- data final igual ao marco: incremento `+1`;
- data final posterior ao marco: incremento `+1`.

Anos bissextos usam o calendário real. Para início em 29 de fevereiro,
28 de fevereiro é o aniversário em ano não bissexto. A soma de meses
também limita o dia ao último dia válido do mês de destino.

## Bloqueios

Permanecem bloqueados contratos não executáveis, múltiplas ocorrências,
sobreposições, períodos abertos, datas ausentes, inválidas ou invertidas.
Não há consolidação de períodos ou agregação de ocorrências.

## Cálculo e explicabilidade

`score = Decimal(anos considerados) × valor normativo Decimal`

O Score registra datas, anos completos, meses e dias residuais, política,
motivo da conversão ou de sua ausência, anos considerados, valor,
fórmula e resultado.

## Casos normativos permanentes

| Período | Anos considerados |
| --- | ---: |
| 5 meses e 29 dias | 0 |
| 6 meses exatamente | 1 |
| 11 meses | 1 |
| 1 ano e 5 meses | 1 |
| 1 ano e 6 meses | 2 |
| 2 anos e 6 meses | 3 |
