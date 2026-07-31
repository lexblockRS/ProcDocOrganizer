# Project Explorer

## Papel atual

`ProjectExplorerWindow` é uma View passiva do Productive Workspace. Ela renderiza
o projeto ativo, coleta edições operacionais e emite solicitações de lifecycle.
Não cria, abre ou fecha Projects por conta própria e não escolhe banco de dados.

O lifecycle oficial é:

```text
ProjectExplorerWindow (solicitação)
    ↓
ProjectController
    ↓
ProjectManager + ProjectSessionFactory
    ↓
ApplicationLifecycleHost
```

## Composição por Project

Depois que a `ProjectSession` candidata foi criada, a aplicação RSC compõe um
`ProjectExplorerApplicationService` ligado ao `database.db` do `.pdop`. Esse
serviço recebe explicitamente os Stores, o `DocumentRepository`, o estado
operacional e a raiz do Workspace. Ele não descobre a sessão, não acessa o
Controller e não sobrevive à troca de Project.

O facade coordena Explorer, Coverage, Insights, Dashboard, Review, Evaluation,
Results e Report com as mesmas dependências project-scoped. O `Project` do SDK
que ele expõe é apenas uma projeção operacional; não é autoridade de lifecycle.

## Estado da View

A View não mantém `_current_project`, `_current_workspace`, Evaluation ou Results
como fontes de verdade. As propriedades exibidas derivam do serviço atualmente
vinculado. Ao fechar ou trocar Project, o composition root desvincula o serviço,
limpa Stores e histórico e descarta as dependências da sessão anterior.

## Persistência

O banco produtivo oficial é sempre:

```text
<project>.pdop/database.db
```

`projects/productive-shell.sqlite` é somente um artefato legado detectado e
preservado. Ele não é aberto, copiado, associado ou migrado automaticamente.

## Fronteiras

A View não acessa SQLite, Stores ou entidades para navegar. O facade não executa
regras normativas fora dos serviços oficiais e não altera Kernel, Pipeline,
Validation ou Compatibility.
