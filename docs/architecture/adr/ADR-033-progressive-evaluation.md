# ADR-033 — Avaliação Progressiva

## Status

Aceito.

## Contexto

O pipeline integrado tratava a ausência de `ExecutionBinding` como erro fatal.
Isso impedia Results Explorer e Evaluation Report de explicarem a pendência
que o usuário precisava resolver.

## Decisão

Adota-se o princípio P-001 — Avaliação Progressiva:

> O ProcDocOrganizer deve ser capaz de produzir avaliações parciais sempre
> que possível. Pendências operacionais não devem impedir a compreensão do
> estado do processo. Somente falhas que impossibilitem tecnicamente a
> execução do Pipeline poderão interromper a avaliação.

Fatos sem Binding não entram no trecho normativo executável e são preservados
como `RSCProcessPendingFact`. Não há Binding automático, inferência de Criterion
ou alteração de pontuação.

O snapshot também preserva todos os Documents de cada Evidence para que uma
avaliação parcial continue integralmente auditável.

## Consequências

- Kernel, Validation, Compatibility e Aggregator permanecem inalterados;
- a pontuação reflete somente fatos explicitamente enquadrados;
- relatórios permanecem disponíveis durante a complementação operacional;
- falhas de integridade que inviabilizam o pipeline continuam fatais.
