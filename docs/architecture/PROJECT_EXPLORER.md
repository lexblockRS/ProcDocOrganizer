# Project Explorer

## Objetivo

`ProjectExplorerWindow` é a composition root visual do fluxo integrado de
Project, Evidence, ExecutionFact, Binding e avaliação. Ela apresenta dados e
coleta intenções sem introduzir regra de negócio ou conhecer SQLite.

## Estrutura visual

```text
Janela principal
├── Barra de título
├── Menu Arquivo
│   ├── Novo Projeto
│   ├── Abrir Projeto
│   ├── Fechar Projeto
│   └── Sair
├── Menu Ajuda
│   └── Sobre
├── Toolbar
│   ├── Novo
│   ├── Abrir
│   └── Fechar
├── Painel do Project
│   ├── Nome
│   ├── Aggregate ID
│   ├── Application
│   ├── Estado
│   ├── Revision
│   ├── Workspace
│   └── Data de criação, quando disponível
└── Barra de status
```

O painel inclui Evidence, ExecutionFacts, enquadramento manual, execução,
Results Explorer e Evaluation Report. OCR, IA e inferência normativa não fazem
parte desse fluxo.

## Novo Projeto

```text
NewProjectDialog
  ↓ nome + Application registrada
ProjectExplorerApplicationService.create_project()
  ↓
ProjectExplorerWindow atualiza o painel
```

O diálogo existente é reutilizado. A raiz de Workspaces configurada na janela
é exibida como destino e permanece fixa para garantir que o Locator consiga
reabrir o ambiente.

## Abrir Projeto

```text
ProjectExplorerApplicationService.list_projects()
  ↓ seleção do usuário
ProjectExplorerApplicationService.open_project()
  ↓
ProjectExplorerWindow atualiza o painel
```

O Project é reidratado com o mesmo `aggregate_id`, estado, revisão e
`application_id`. Workspace é localizado pela identidade e não é recriado.

## Fechar Projeto

Fechar remove somente as referências correntes da janela e limpa o painel.
Não remove a linha SQLite e não altera ou exclui o Workspace.

Fechar a aplicação encerra a conexão mantida pelo Store. Na próxima execução,
uma nova janela pode abrir o mesmo banco e localizar o mesmo Workspace.

## Responsabilidades

A janela:

- apresenta metadados do Project;
- coleta intenção por dialogs e actions;
- chama somente o `ProjectExplorerApplicationService` e ViewModels;
- mantém apenas o Project atualmente exibido;
- comunica resultado na barra de status.

A janela não:

- altera invariantes do Project;
- executa Kernel, Validation ou Compatibility;
- cria ou edita aggregates diretamente;
- acessa tabelas SQLite diretamente;
- cria diretórios fora do Workspace.

## Integração com a plataforma

Uma factory de composição constrói o Application Service com Registry, Stores,
WorkspaceFactory e WorkspaceLocator. Essa factory é a única fronteira deste
fluxo que conhece os adapters concretos; `ui/project_explorer.py` não importa
`database`.

Essa composição mantém UI, domínio e infraestrutura com responsabilidades
distintas, embora reunidas concretamente nesta primeira janela funcional.
