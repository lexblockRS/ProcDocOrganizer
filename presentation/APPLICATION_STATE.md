# Contrato de Estado da Aplicação

O estado descrito aqui pertence exclusivamente à apresentação. Ele não
representa status, validação, pontuação ou qualquer regra do Processo RSC.

## Estados

- `NO_PROJECT`: nenhum projeto está associado à UI.
- `PROJECT_OPEN`: há projeto aberto e sem alterações pendentes.
- `PROJECT_MODIFIED`: há projeto aberto com alterações pendentes.
- `BUSY`: uma operação temporária está em andamento.
- `ERROR`: uma operação ou transição terminou em erro.
- `CLOSING`: encerramento iniciado; estado terminal.

## Transições diretas

| Origem | Destinos |
|---|---|
| `NO_PROJECT` | `PROJECT_OPEN`, `ERROR`, `CLOSING` |
| `PROJECT_OPEN` | `NO_PROJECT`, `PROJECT_MODIFIED`, `ERROR`, `CLOSING` |
| `PROJECT_MODIFIED` | `NO_PROJECT`, `PROJECT_OPEN`, `ERROR`, `CLOSING` |
| `ERROR` | `NO_PROJECT`, `PROJECT_OPEN`, `PROJECT_MODIFIED`, `CLOSING` |
| `BUSY` | somente pelo ciclo da operação |
| `CLOSING` | nenhum |

`BUSY` é iniciado exclusivamente por `begin_operation()`.
`complete_operation()` restaura o estado anterior por padrão e pode
receber um estado final estável. `cancel_operation()` sempre restaura o
estado anterior. `fail_operation()` produz `ERROR`.

## Invariantes

- `NO_PROJECT` não possui projeto nem modificação.
- `PROJECT_OPEN` possui projeto e não possui modificação.
- `PROJECT_MODIFIED` possui projeto e modificação.
- `BUSY` possui estado anterior e identificador de operação.
- `ERROR` possui mensagem.
- `CLOSING` é terminal.

O `ApplicationStateStore` é o único proprietário do snapshot. Cada
mudança bem-sucedida cria uma nova instância imutável, incrementa a
revisão e notifica observers. Transições recusadas preservam snapshot,
revisão e observers.
