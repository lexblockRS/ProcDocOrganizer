# Contrato do NavigationController

O `NavigationController` pertence à camada de coordenação. Ele não é Store,
não possui snapshot, revisão, observers ou histórico. Sua única função é
coordenar as APIs públicas de `PerspectiveStore`, `WorkspaceStore` e
`SelectionStore`.

## Coordenação e estado

Os stores permanecem proprietários de todo estado. O controller mantém somente
referências às dependências necessárias e não duplica seus valores.

## Fluxo

`navigate_to(perspective_id)`:

1. valida o `PerspectiveId`;
2. solicita sua ativação ao `PerspectiveStore`;
3. solicita sua montagem lógica ao `WorkspaceStore`;
4. limpa o `SelectionStore`, quando essa política estiver habilitada.

Se uma etapa falhar, o fluxo é interrompido imediatamente e a exceção original
é propagada sem tratamento ou mascaramento. Não há rollback ou compensação
manual nesta etapa. Chamadas redundantes permanecem no-op porque os stores
preservam essa invariante.

## Responsabilidades e limitações

O controller não cria widgets, executa factories, abre ou salva projetos,
consulta domínio ou infraestrutura, mantém histórico, implementa
voltar/avançar ou breadcrumbs. Ele também não conhece Qt, MainWindow,
`ApplicationStateStore`, `PresentationContextStore` ou `ApplicationFacade`.

Rollback, transações de interface e compensações pertencem a uma etapa futura,
caso a integração efetiva torne essa complexidade necessária.
