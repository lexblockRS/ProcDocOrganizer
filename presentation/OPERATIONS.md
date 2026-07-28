# Contrato de Operações

O `OperationExecutor` é um componente de coordenação síncrono e independente
de framework gráfico. Ele não é Store e não possui snapshot, revisão,
observers, fila, histórico ou cache. Seu único estado duradouro é a referência
ao `ApplicationStateStore`, proprietário do ciclo operacional.

## Valores do contrato

`OperationId` é um identificador textual imutável, normalizado, hashable e
serializável. `OperationContext` associa esse ID a um `CancellationToken` e é
entregue à unidade de trabalho.

O token oferece cancelamento cooperativo: solicitar cancelamento apenas marca
o sinal. A unidade de trabalho pode chamar
`throw_if_cancellation_requested()`. Nenhuma thread ou processo é interrompido
à força.

## API e fluxos

```python
token = CancellationToken()
result = executor.execute(
    OperationId("load-project"),
    lambda context: load_data(context.cancellation_token),
    cancellation_token=token,
)
```

A API escolhida é
`execute(operation_id, work, cancellation_token=None)`. Ela permite que o
chamador retenha o token antes da execução sem introduzir `prepare()` ou uma
segunda forma de executar.

No sucesso, o executor inicia o ciclo, verifica cancelamento, executa `work`,
verifica novamente, conclui o ciclo e devolve o resultado sem transformação.
A verificação posterior reconhece cancelamentos solicitados durante um
trabalho que retorne normalmente.

`OperationCancelled` restaura o estado anterior por `cancel_operation()` e é
propagada. Outras exceções são registradas por `fail_operation()` e também são
propagadas com seu traceback. Uma falha secundária ao atualizar o Store é
registrada, mas não mascara a exceção original. Falha em `begin_operation()`
impede a execução de `work` e não aciona finalização.

## Limites

Não existem Qt, execução assíncrona, threads criadas pelo executor, widgets,
notificações, navegação, domínio, infraestrutura, persistência, retry ou
rollback de negócio. Um adaptador futuro poderá chamar este mesmo núcleo em
background; a sinalização do token já é segura para esse uso, sem contaminar o
contrato central com afinidade de UI.
