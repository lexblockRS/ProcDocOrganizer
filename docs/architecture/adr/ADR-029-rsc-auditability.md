# ADR-029 — Auditabilidade dos objetos RSC

## Status

Aceito.

## Contexto

FunctionalAssignmentEvidence, FunctionalExercise e Activity ainda não possuem
metadados completos de auditoria.

## Decisão

Esta etapa não adiciona timestamps, autoria ou histórico parcial. Antes da
pontuação será desenhada uma governança coerente que avalie `created_at`,
`updated_at`, autoria, justificativas, origem da decisão, histórico e versão
do regulamento.

## Consequências

O pipeline funcional permanece estável. Resultados normativos não serão
considerados plenamente auditáveis até essa governança e suas migrations
serem implementadas em sprint própria.
