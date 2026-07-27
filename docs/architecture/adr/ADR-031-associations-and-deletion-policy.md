# ADR-031 — Associações e política de exclusão

## Status

Aceito.

## Contexto

Activity e FunctionalExercise usam UUIDs e tabelas associativas ordenadas. A
exclusão do proprietário remove suas associações por cascade; destinos
funcionais relacionados são protegidos. A fronteira com Evidence/documento
usa referência histórica textual.

## Decisão

O agregado proprietário controla somente sua associação. Exclusões futuras
serão operações explícitas e não poderão destruir silenciosamente a
rastreabilidade. Referências relacionais fortes continuam protegidas e
referências históricas textuais seguem a política do ADR-028.

## Consequências

Não há alteração de schema nesta sprint. Uma futura capacidade de exclusão
deverá definir autorização, impacto, retenção e comunicação visual antes de
modificar dados relacionados.
