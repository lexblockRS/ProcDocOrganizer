# ADR-028 — Referências históricas e fontes removidas

## Status

Aceito.

## Contexto

A cadeia RSC preserva UUIDs e referências textuais mesmo quando uma Evidence
ou um documento deixa de estar disponível. Ausência do destino não equivale à
ausência da relação histórica.

## Decisão

Referências históricas não serão apagadas nem reescritas automaticamente. A
interface deve exibir o ID, o tipo da relação e sua indisponibilidade. A
navegação permanece desabilitada quando o destino não pode ser resolvido.
Exclusões futuras deverão respeitar essa política.

## Consequências

Órfãos históricos são deliberadamente possíveis na fronteira documental.
Isso preserva auditabilidade, exige mensagens explícitas e demanda uma
política formal de exclusão antes de operações destrutivas amplas. Nenhuma
foreign key ou migration é introduzida por esta decisão.
