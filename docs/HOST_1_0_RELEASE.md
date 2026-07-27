# ProcDocOrganizer — Platform Host 1.0

## Escopo da Release 1.1

A Release 1.1 conclui a fundação do Platform Host 1.0. O Host passa a
descobrir Applications por contratos neutros, compor sessões de projeto,
instalar contribuições de apresentação e executar automaticamente o lifecycle
dos módulos, sem exigir branches por Application nesses fluxos.

Esta declaração cobre a infraestrutura de plataforma. Ela não declara
conclusão funcional do domínio RSC nem introduz funcionalidades da Release
1.2.

## Arquitetura final do Host

O composition root registra as Applications no `ApplicationRegistry` e
compõe `ProjectSessionFactory`, `ProjectController` e o instalador de
contribuições. O fluxo produtivo é:

```text
ApplicationRegistry
    → ApplicationDescriptor
    → criação/abertura de Project
    → ProjectSessionFactory
    → PlatformSession + ApplicationRuntime
    → ApplicationLifecycleHost
    → instalação e descarte
```

`ProjectSession` permanece como envelope de compatibilidade dos serviços
existentes. Sua `PlatformSession` reúne o contexto permanente do projeto, o
contexto de serviços compartilhados e o runtime da Application.

## Componentes neutros

- `ApplicationDescriptor`: identidade e compatibilidade estáticas.
- `ApplicationModule`: contrato de preparação, sessão, contribuições,
  transições e descarte.
- `ApplicationRegistry`: catálogo determinístico de módulos, híbridos e
  Applications legadas.
- `ProjectContext` e `SessionContext`: contextos fornecidos pelo Host.
- `PlatformSession`: agregado neutro da sessão.
- `ApplicationRuntime`: autoridade sobre estado e hooks do módulo.
- `ApplicationLifecycleHost`: fronteira usada pelo fluxo de projeto para
  ativar e descartar runtimes.
- `ContributionManager` e instaladores: catálogo e materialização das
  contribuições.

## Lifecycle implementado

O contrato vigente utiliza os seguintes estados:

```text
REGISTERED
    → PROJECT_PREPARED
    → SESSION_CREATED
    → PRESENTATION_MOUNTED
    → ACTIVE
    → DEACTIVATING
    → DISPOSED
```

`PROJECT_PREPARED` corresponde ao marco conceitual PREPARED e
`DEACTIVATING` ao marco DISPOSING. `PRESENTATION_MOUNTED` registra
explicitamente que a apresentação foi instalada antes de a Application ficar
ativa.

O Runtime garante uma preparação, uma criação de sessão e um descarte por
ciclo. Chamadas inválidas são rejeitadas. O descarte é idempotente. Falhas em
callbacks de transição ou descarte são registradas, e o Runtime conclui em
estado consistente. Falha na criação da sessão aciona descarte compensatório
dos recursos preparados.

## Bridges preservadas

- `ProjectSession` continua envolvendo `PlatformSession`.
- `ProjectSession.application` permanece disponível para consumidores
  históricos.
- `ProjectSession.rsc_session` continua como alias transitório da sessão RSC.
- Applications legadas continuam recebendo descriptors transitórios.
- Os caminhos históricos de serviços e controllers permanecem ativos.

Essas bridges são compatibilidade deliberada; sua remoção não pertence à
Release 1.1.

## Limitações conhecidas

- O composition root ainda registra explicitamente a Application RSC.
- Partes históricas do `ProjectController` ainda coordenam funcionalidades
  específicas já existentes.
- `ProjectSession` e `PlatformSession` coexistem enquanto houver consumidores
  da API histórica.
- Não existe discovery dinâmico de plugins nem SDK público.
- Algumas decisões da plataforma ainda não possuem ADR formal dedicado.

## ADRs e decisões aplicadas

A Release preserva os ADRs aceitos existentes. O ADR-007, sobre camada de
apresentação e projeções, fundamenta a separação do Dashboard. Os ADRs
documentais e do domínio RSC continuam vigentes, mas não foram modificados
por esta release.

As decisões de plataforma consolidadas entre PF-02 e PF-06E — contratos de
Application, Registry, PlatformSession, contribuições e lifecycle — estão
registradas na documentação de validação do Core e nesta declaração de
release. A ausência de um ADR exclusivo do Platform Host permanece uma
limitação documental conhecida.

## Critérios para iniciar a Release 1.2

A Release 1.2 somente deve começar sobre uma baseline em que:

- a suíte integral, `compileall` e `git diff --check` estejam aprovados;
- o catálogo por descriptors continue sendo a única fonte do fluxo Novo
  Projeto;
- hooks de lifecycle permaneçam centralizados no Host;
- bridges de compatibilidade não sejam removidas implicitamente;
- qualquer mudança de contrato ou remoção de bridge seja precedida por
  decisão arquitetural explícita.

## Estado consolidado na Release 1.2

As limitações acima registram fielmente o encerramento da Release 1.1. Durante
a Release 1.2, sem alterar o comportamento funcional do Host, foram
estabilizados:

- o namespace público `platform_sdk`;
- contratos públicos de Menu, Action, View, Toolbar e Dashboard;
- materialização de apresentação pelo Host sem exposição de Qt às
  Applications;
- discovery automático e determinístico por `ApplicationProvider`;
- coexistência das Applications RSC e Asset Audit;
- Asset Audit como Application de referência para isolamento, lifecycle e
  contribuições públicas.

Continuam deliberadamente preservadas as bridges de compatibilidade descritas
neste documento. Plugins externos, hot reload e remoção das APIs históricas
não fazem parte da plataforma 1.2.
