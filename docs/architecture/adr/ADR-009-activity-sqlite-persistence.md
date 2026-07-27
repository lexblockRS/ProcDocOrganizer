# ADR-009 — Persistência SQLite de Activity

## Status

Aceito.

## Contexto

O ADR-008 consolidou `Activity`, seus estados e suas referências tipadas, mas
essas informações permaneciam apenas no `InMemoryActivityRepository` e eram
perdidas ao reabrir um projeto.

## Decisão

Cada banco de projeto passa a armazenar atividades em `rsc_activities`.
As relações muitos-para-muitos são armazenadas separadamente em
`rsc_activity_functional_assignment_evidences` e
`rsc_activity_functional_exercises`. Ambas preservam a ordem do modelo por um
campo `ordinal`, impedem duplicidades e usam chaves estrangeiras.

`Activity` não é proprietária de evidências nem exercícios. A exclusão da
atividade remove somente suas associações por `ON DELETE CASCADE`; nenhuma
cascata parte das associações para as entidades relacionadas. A remoção de
atividade não integra a port nesta etapa.

## Reidratação

O repository lê a linha principal e as duas coleções ordenadas, reconstrói
`ActivityState` e os identificadores tipados e invoca o construtor público de
`Activity`. Portanto, todas as invariantes do domínio também são verificadas
na leitura. Não são executadas transições artificiais para alcançar o estado
persistido.

## Atualização imutável e transação

A port `ActivityRepository` passa a expor `save(activity)`. A operação recebe
a nova versão imutável, valida a existência de todas as relações e, em uma
única transação:

1. insere ou atualiza os dados principais;
2. substitui integralmente as relações com evidências;
3. substitui integralmente as relações com exercícios.

Qualquer falha reverte toda a operação. `add(activity)` permanece disponível
para o caso de uso de criação e rejeita identidade já existente.

## Integridade e cardinalidades

Cada `Activity` relaciona-se a zero ou muitas evidências e zero ou muitos
exercícios. Uma evidência ou exercício pode aparecer em várias atividades.
Uma relação ausente impede a gravação. As chaves estrangeiras também impedem
a remoção de evidências ou exercícios enquanto relacionados.

## Compatibilidade

A migration v6 cria somente as três novas tabelas e seus índices, preservando
todos os dados anteriores. Projetos na versão 5 são atualizados pelo mecanismo
incremental existente; novas aberturas na versão 6 não reaplicam a migration.
A composição em memória continua usando `InMemoryActivityRepository`, enquanto
a composição SQLite passa a usar `SQLiteActivityRepository`.
