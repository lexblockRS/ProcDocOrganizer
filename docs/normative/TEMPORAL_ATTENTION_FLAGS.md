# Temporal Attention Flags

## Finalidade

Temporal Attention Flags são indicadores exclusivamente informativos
para a interface e para a revisão humana. Eles não fazem parte da
execução normativa e nunca:

- alteram pontuação;
- alteram anos considerados;
- bloqueiam execução;
- modificam contratos;
- modificam validações;
- substituem decisão humana.

O `TemporalAttentionAnalyzer` recebe `CriterionScoreCollection` já
produzida e devolve uma coleção independente. Cada alerta referencia
`score_id`, `contract_id` e `criterion_id`, permitindo que a interface o
apresente junto ao resultado sem incorporá-lo ao contrato normativo.

## Estrutura

`TemporalAttention` é imutável e contém:

- `code`;
- `severity`;
- `message`;
- `explanation`;
- referências ao Score, contrato e critério.

`TemporalAttentionCollection` preserva a ordem, rejeita códigos
duplicados para o mesmo Score e permite consulta por `score_id`.

## Códigos

### `EXACT_SIX_MONTH_LIMIT`

Resíduo de exatamente seis meses-calendário e zero dias. Indica que o
período coincide com o limite oficial de conversão.

### `JUST_BELOW_SIX_MONTH_LIMIT`

Resíduo superior a cinco meses e inferior a seis meses. Pequena mudança
documental pode alterar os anos considerados.

### `JUST_ABOVE_SIX_MONTH_LIMIT`

Resíduo superior a seis meses e inferior a sete meses. Recomenda
conferência das datas documentais.

### `LEAP_DAY_INVOLVED`

Data inicial ou final igual a 29 de fevereiro.

### `EXACT_TEMPORAL_LANDMARK`

Data final coincidente com um aniversário completo ou com o marco exato
de seis meses-calendário.

## Severidades

- `INFO`: marco de calendário que merece visibilidade.
- `WARNING`: proximidade de fronteira que recomenda conferência.

Severidade não corresponde a estado normativo e não bloqueia cálculo.

## Reutilização temporal

O analisador consome a mesma `TemporalDecomposition` canônica usada
pelas regras temporais. Ele não implementa cálculo próprio de datas.
