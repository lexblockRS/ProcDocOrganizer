# Contrato do Workspace

O Workspace representa o espaço central lógico no qual uma perspectiva será
apresentada futuramente. Ele não é uma janela, tela, view, widget ou Processo
RSC.

Nesta etapa, “montar” significa somente registrar um `PerspectiveId` como
presente no espaço de trabalho. Nenhuma factory é executada e nenhum componente
visual é criado.

## Elementos

- `WorkspaceState.EMPTY`: nenhuma perspectiva está montada.
- `WorkspaceState.READY`: existe exatamente uma perspectiva montada.
- `WorkspaceSnapshot`: DTO imutável com estado, perspectiva ativa e revisão.
- `WorkspaceStore`: único proprietário do snapshot lógico do Workspace.

## Responsabilidades

O store consulta o catálogo do `PerspectiveStore` apenas para confirmar que o
ID solicitado está registrado. Ele não ativa perspectivas, não assina o
catálogo e não modifica o store consultado. `mount()` monta ou substitui uma
perspectiva logicamente; `clear()` retorna ao estado vazio.

## Invariantes

- `EMPTY` sempre possui `active_perspective=None`.
- `READY` sempre possui exatamente um `PerspectiveId`.
- Montagem, substituição e limpeza efetivas incrementam a revisão.
- Montagem ou limpeza redundante preserva snapshot e revisão.
- Snapshots são imutáveis e falhas de observers são isoladas.
- Factories nunca são executadas.
- Não existem Qt, widgets, MainWindow, toolbar, menu, domínio, navegação,
  persistência ou integração com `ApplicationFacade`.
