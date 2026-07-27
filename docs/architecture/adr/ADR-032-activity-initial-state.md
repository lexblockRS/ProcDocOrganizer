# ADR-032 — Estado inicial de Activity

## Status

Aceito.

## Contexto

A existência de uma Activity registra uma lembrança ou hipótese funcional,
mas não comprova nem classifica o fato.

## Decisão

Toda Activity criada pelo fluxo atual nasce em `REMEMBERED`. Criação não
significa investigação, comprovação ou enquadramento RSC. Transições pertencem
a casos de uso específicos, e a futura camada normativa não inferirá
comprovação pela mera existência da Activity.

## Consequências

O significado atual permanece inalterado e nenhuma transição nova é criada.
