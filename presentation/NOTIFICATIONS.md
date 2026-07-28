# Contrato de Notificações

Notificações são eventos transitórios da camada de apresentação. Elas não
representam estado da aplicação e não são persistidas.

## Elementos

`NotificationLevel` possui somente `INFO`, `SUCCESS`, `WARNING` e `ERROR`.

`Notification` é um DTO imutável, slotted, hashable e serializável. Ele contém
nível, título, mensagem e timeout opcional. O timeout é expresso em segundos,
aceita números não negativos e não possui relação com APIs de Qt.

`NotificationCenter` é um componente de coordenação, não um Store. Ele mantém
apenas os callbacks atualmente inscritos, na ordem de inscrição.

## Publicação

`publish(notification)` valida o DTO e o entrega diretamente a cada observer.
A mesma instância imutável é recebida por todos. Uma falha é registrada e não
impede a entrega aos callbacks seguintes.

`subscribe(callback)` devolve uma função de cancelamento idempotente. Inscrever
o mesmo callback novamente não duplica sua entrega.

## Limitações

Não existem snapshot, revisão, fila, replay ou histórico. O centro não cria
widgets, mostra diálogos, escreve em status bar, navega, altera Stores ou
consulta domínio, infraestrutura ou persistência. A integração com
consumidores visuais pertence a uma etapa futura.
