# Requirement Score

## Objetivo

`RequirementScore` é a consolidação imutável de todos os
`CriterionScore` que possuem o mesmo `requirement_id`. Cada requisito
presente na entrada produz exatamente um resultado. Uma coleção de
critérios vazia produz uma coleção de requisitos vazia.

## Estrutura

O modelo preserva:

- identidade estável do resultado;
- identidade do requisito;
- todos os Scores de critérios, na ordem original;
- Scores executados;
- Scores bloqueados;
- Scores ignorados pela soma;
- total em `Decimal`;
- trace estruturado da agregação;
- explicação legível.

Como os objetos originais são mantidos nas tuplas, permanecem acessíveis
os contratos de origem, traces de execução, operandos, fórmulas e
referências normativas de cada cálculo.

`RequirementScore`, `RequirementAggregationTrace` e
`RequirementScoreCollection` são imutáveis e slotted. A coleção rejeita
identidades ou requisitos duplicados.

## Limites

O modelo não representa eixo, processo, elegibilidade ou ranking. Ele
não executa regra de contagem e não modifica `CriterionScore`.
