# Contrato do Presentation Context

O Presentation Context fornece uma visão consolidada do estado global da
camada de apresentação. Ele existe para que futuros componentes de
orquestração observem um único snapshot sem criarem dependências diretas entre
os stores existentes.

## Arquitetura

```text
ApplicationStateStore ─┐
SelectionStore ────────┼──> PresentationContextStore
PerspectiveStore ──────┘              │
                                      └──> PresentationSnapshot
```

`ApplicationStateStore`, `SelectionStore` e `PerspectiveStore` continuam sendo
as fontes autoritativas de seus estados. O `PresentationContextStore` observa
esses stores e é proprietário somente do snapshot consolidado derivado. Ele
não envia comandos, não altera estados de origem e não substitui seus
proprietários.

## Elementos

`PresentationSnapshot` é um DTO imutável e slotted que referencia os três
snapshots internos e possui uma revisão própria.

`PresentationContextStore` captura os snapshots iniciais, assina os três
stores e publica uma nova consolidação quando um deles muda efetivamente.
Observers recebem somente o `PresentationSnapshot`; a função de cancelamento
da assinatura é idempotente e falhas são isoladas.

## Responsabilidades e invariantes

- Os snapshots internos são preservados por referência e nunca modificados.
- Cada alteração efetiva cria um novo snapshot e incrementa uma revisão.
- Atualizações redundantes não alteram snapshot, revisão ou observers.
- O Context Store não abre ou salva projetos, seleciona elementos, troca
  perspectivas, navega ou cria widgets.
- O contrato não conhece Qt, MainWindow, Workspace, domínio, infraestrutura
  ou `ApplicationFacade`.
