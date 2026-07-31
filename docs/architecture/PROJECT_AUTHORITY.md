# Project Authority

## Autoridade única

`ApplicationLifecycleHost.current_session` é a única autoridade sobre o
Project ativo. O Host é criado uma vez pela composition root e injetado no
`ProjectController` e na projeção compatível `ProjectState`. Não existe singleton,
variável global ou lookup por Service Locator.

`ProjectManager` permanece stateless e cuida somente da estrutura física do
`.pdop`. `ProjectController` recebe comandos e coordena o lifecycle, mas não
armazena sessão. `ProjectState.current_project` deriva da sessão oficial.

## Abertura e troca transacionais

```text
validar .pdop
    → criar ProjectSession candidata
    → preparar runtime e repositories
    → compor consumidores project-scoped
    → ativar runtime candidato
    → publicar current_session
    → vincular todos os consumidores
    → invalidar contexto visual anterior
    → descartar serviços e runtime anteriores
```

A sessão anterior continua oficial durante toda a preparação. Falha antes da
publicação descarta apenas a candidata. Falha na vinculação final restaura a
sessão e os consumidores anteriores, preservando Workspace, Results e histórico.
A sessão anterior só é descartada depois do commit integral.

## Fechamento

O fechamento desvincula e descarta serviços project-scoped, limpa Workspace,
Selection e Navigation History, remove `current_session` e, por fim, descarta o
runtime. Se a invalidação dos consumidores falhar, o serviço anterior é
religado e a sessão oficial é preservada.

## Revisões independentes

`OperationalProjectStateStore` usa o armazenamento chave–valor `index_state` já
existente no `database.db`, sem migration. Ele mantém uma identidade operacional
estável e uma revisão monotônica por `.pdop`. Mutações de Documents, Evidences,
ExecutionFacts e Bindings incrementam essa revisão.

As três revisões não se substituem:

- operational revision: fonte de `CoverageInput.project_revision`;
- Workspace revision: transições visuais de `WorkspaceSnapshot`;
- Evaluation revision: snapshot produzido pelo processo de avaliação.

`platform_sdk.Project.revision` não é autoridade operacional e a
`ProjectSession` congelada não recebeu contador mutável.

## Documents e Coverage

O catálogo canônico vem de `DocumentRepository.list_all()`. As relações com
Evidence são projetadas separadamente. Portanto, Document sem Evidence continua
presente no `CoverageInput`, recebe `ResourceIdentity` pelo UUID canônico e pode
originar Finding, Insight, Review e inspeção explicáveis.

## Legado produtivo

Se `productive-shell.sqlite` existir, a composition root registra aviso técnico
e preserva seus bytes. A abertura do `.pdop` não é bloqueada. Não há leitura,
cópia, associação por nome, exclusão ou importação automática nesta release.
