# Requirement Aggregation

## Entrada e saída

`RequirementScoreAggregator` recebe somente
`CriterionScoreCollection` e devolve `RequirementScoreCollection`.
Os Scores são agrupados por `requirement_id`, preservando a ordem da
primeira ocorrência dos requisitos e a ordem dos critérios em cada
grupo.

## Regra de soma

Somente Scores com `scoring_state = EXECUTED` participam:

`total_score = soma Decimal dos calculated_score executados`

O valor inicial é `Decimal(0)`. Scores `BLOCKED`, `TEXT_DEPENDENT`,
`NOT_EXECUTED` ou `HUMAN_REVIEW_REQUIRED` não somam e não são
descartados.

## Explicabilidade

O trace registra:

- todos os IDs de Scores recebidos;
- IDs executados;
- IDs bloqueados;
- IDs ignorados;
- critérios participantes;
- operação `DECIMAL_SUM_EXECUTED_ONLY`.

A explicação informa as quantidades total, executada e bloqueada, os
estados ignorados, os critérios participantes e o total produzido.

## Restrições

Não existe interpretação normativa, nova regra, busca de dados,
agregação entre requisitos, `AxisScore`, `ProcessScore`, elegibilidade
ou ranking.
