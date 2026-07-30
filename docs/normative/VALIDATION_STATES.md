# Estados da Validação de Execução

## READY

O contrato possui fatos, documentos, medição, unidade, período e rastreabilidade
consistentes; não há revisão, dependência textual ou alerta.

Não significa que o critério foi atendido.

## READY_WITH_WARNINGS

O contrato está estruturalmente completo, mas conserva alertas não bloqueantes.
Os alertas permanecem visíveis e não são corrigidos.

## BLOCKED

Existe ao menos um impedimento estrutural:

- fato requerido ausente;
- documento ausente;
- medição ausente;
- unidade incompatível;
- período inválido;
- duplicidade de tipo factual;
- rastreabilidade quebrada;
- divergência entre fato, regra e manifesto.

## HUMAN_REVIEW_REQUIRED

O contrato não possui bloqueio estrutural, mas exige revisão por:

- variante pendente;
- sobreposição `POSSIBLE`, `CONFIRMED` ou `UNKNOWN`;
- revisão humana já exigida pelo Assessment.

O estado não autoriza seleção ou resolução automática.

## TEXT_DEPENDENT

O contrato está estruturalmente completo, porém sua regra possui
`computability_level = TEXT_DEPENDENT`. O texto normativo continua necessário.

## Matriz de precedência

| Condição | Estado |
|---|---|
| bloqueio estrutural | `BLOCKED` |
| revisão humana, sem bloqueio | `HUMAN_REVIEW_REQUIRED` |
| dependência textual, sem bloqueio/revisão | `TEXT_DEPENDENT` |
| somente alertas | `READY_WITH_WARNINGS` |
| nenhuma pendência | `READY` |

## Semântica

Todos os estados descrevem o contrato factual, nunca satisfação do critério,
pontuação, elegibilidade ou decisão administrativa.
