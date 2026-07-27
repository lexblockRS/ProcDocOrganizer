# ProcDocOrganizer — Baseline Arquitetural 1.1

## Status

Esta é a baseline oficial do Platform Host 1.0, estabelecida pelo EP-00 da
Release 1.2. Ela congela a superfície arquitetural entregue ao final da
Release 1.1. Mudanças posteriores no Host, em seus contratos estáveis ou nas
invariantes abaixo devem ser tratadas como decisões arquiteturais deliberadas.

## Visão geral

O ProcDocOrganizer é uma plataforma desktop que hospeda Applications sobre
serviços compartilhados de documentos e conhecimento. O Host seleciona uma
Application pelo projeto, compõe uma sessão, fornece contextos neutros,
instala contribuições e conduz o lifecycle do módulo.

```text
Composition Root
    → ApplicationRegistry
    → ApplicationDescriptor / ApplicationModule
    → ProjectSessionFactory
    → ProjectSession
        → PlatformSession
            → ProjectContext
            → SessionContext
            → ApplicationRuntime
    → contribuições
    → lifecycle
```

## Responsabilidades do Host

O Host:

- registra e resolve Applications;
- valida identidade, versão da plataforma e schema de projeto;
- cria os serviços compartilhados associados ao projeto;
- fornece `ProjectContext` e `SessionContext`;
- cria, publica, ativa e descarta a sessão da Application;
- mantém o estado do lifecycle;
- cataloga e instala contribuições declarativas;
- oferece navegação e apresentação compartilhadas;
- preserva bridges necessárias aos consumidores históricos.

O Host não contém regras de negócio específicas de uma Application, não deve
interpretar o domínio RSC e não deve selecionar comportamento por IDs
específicos.

## APIs estáveis

As seguintes APIs, em seus módulos canônicos atuais, são estáveis a partir
desta baseline:

| API | Módulo canônico | Responsabilidade estável |
|---|---|---|
| `ApplicationModule` | `contracts.application_module` | Contrato de módulo, sessão, contribuições e lifecycle |
| `ApplicationDescriptor` | `contracts.application_descriptor` | Identidade e compatibilidade estáticas |
| `ApplicationRuntime` | `core.application_runtime` | Estado, publicação da sessão e execução dos hooks |
| `PlatformSession` | `core.platform_session` | Agregado neutro da sessão da plataforma |
| `ContributionManager` | `core.contribution_manager` | Registro e consulta determinística de contribuições |
| `DashboardContribution` | `contracts.dashboard_contribution` | Contribuição declarativa para o Dashboard |
| `ProjectSessionFactory` | `core.project_session_factory` | Composição da sessão completa de projeto |
| `ApplicationRegistry` | `core.application_registry` | Catálogo e resolução de Applications |
| Lifecycle | `contracts.lifecycle` | Estados, transições válidas e valor de transição |

Também são contratos públicos de suporte `ProjectContext`, `SessionContext`,
`ContributionRegistration`, `ContributionCategory`, capabilities e os
contratos de contribuição exportados pelo namespace `platform_sdk`.

O Public Platform SDK estabiliza ainda:

- `ApplicationCatalog` e `ApplicationProvider`, para discovery determinístico;
- `MenuContribution`, `ActionContribution`, `ViewContribution` e
  `ToolbarContribution`;
- `ApplicationView`, `ApplicationController`, `DashboardCard` e
  `DashboardPanel`.

Esses contratos não expõem Qt. O Host permanece responsável pela
materialização dos componentes visuais.

Estabilidade significa preservação de responsabilidade, semântica e
compatibilidade. Não significa que toda classe seja reexportada por
`core.__init__`; consumidores devem usar os módulos canônicos indicados.

Ícones não integram o contrato estável de `ApplicationDescriptor`. A
identidade visual permanece responsabilidade da apresentação do Host até que
exista uma necessidade funcional e uma decisão arquitetural específica.

## Componentes internos

São detalhes do Host, não APIs para Applications:

- composition root em `core.application`;
- `ProjectController` e demais controllers;
- `ApplicationLifecycleHost`;
- instaladores Qt de contribuições;
- `MainWindow`, Views, Dialogs e widgets;
- serviços concretos, repositories e adaptadores SQLite;
- métodos, atributos e dataclasses prefixados com `_`;
- bridges e aliases descritos na seção própria.

Applications não devem importar esses componentes.

## Invariantes arquiteturais

1. O Host depende de contratos neutros; aplicações dependem desses contratos,
   nunca de outra aplicação.
2. `application_id` é a identidade persistível e estável de uma Application.
3. O Registry contém uma entrada lógica e um descriptor por Application e
   mantém ordenação determinística.
4. O fluxo Novo Projeto consome descriptors, não objetos concretos.
5. A Factory é a autoridade de composição da sessão.
6. `PlatformSession` reúne exatamente contexto do projeto, contexto de sessão
   e runtime.
7. O Runtime é a única autoridade que chama `prepare()`, `create_session()` e
   `dispose()` no módulo.
8. O lifecycle não regride, não pula estados e não permite dupla execução.
9. A Application somente fica ativa após criação da sessão e montagem da
   apresentação.
10. O descarte é idempotente e termina em `DISPOSED`, inclusive quando o hook
    do módulo falha.
11. Contribuições são declarativas, identificadas pela Application e
    consultadas em ordem determinística.
12. MainWindow e Dashboard não conhecem Applications concretas.
13. Nenhuma nova Application pode exigir um branch por ID no Host.

## Lifecycle estabilizado

O fluxo contratual vigente é:

```text
REGISTERED
    → PROJECT_PREPARED
    → SESSION_CREATED
    → PRESENTATION_MOUNTED
    → ACTIVE
    → DEACTIVATING
    → DISPOSED
```

`PROJECT_PREPARED` representa PREPARED; `DEACTIVATING` representa DISPOSING.
Falha em preparação impede a criação. Falha na criação provoca descarte
compensatório. Falhas de callback são registradas sem corromper o estado.

## Bridges preservadas

As seguintes superfícies existem para compatibilidade, mas não são APIs para
novas Applications:

- `ProjectSession` como envelope externo de `PlatformSession`;
- `ProjectSession.application`;
- `ProjectSession.rsc_session`;
- criação de descriptor transitório para Application legada;
- `ApplicationRegistry.applications` e resolução pelo contrato legado
  `Application`;
- aliases históricos reconhecidos pelo Registry;
- controllers e serviços históricos ainda expostos pela sessão antiga.

Bridges não podem ser removidas incidentalmente. Sua evolução exige decisão
arquitetural, plano de migração e testes de compatibilidade.

## Pontos experimentais

Não fazem parte da API estável:

- carregamento de plugins externos;
- hot reload e unload dinâmico;
- remoção de `ProjectSession` ou de aliases históricos.

## Limitações conhecidas

- `ProjectSession` e `PlatformSession` coexistem.
- Há coordenação histórica específica no `ProjectController`.
- A política futura de plugins ainda não está definida.
- O discovery atual é local e baseado em providers sob o pacote
  `applications`; não é um carregador de plugins externos.

## Regras para novas Applications

Uma nova Application deve:

- implementar `ApplicationModule`;
- fornecer um `ApplicationProvider` descobrível em seu módulo `provider`;
- fornecer um `ApplicationDescriptor` estático e válido;
- importar contratos de plataforma exclusivamente de `platform_sdk`;
- receber recursos exclusivamente por `SessionContext`;
- manter domínio, serviços e persistência próprios fora do Host;
- declarar contribuições pelos contratos da plataforma;
- respeitar o lifecycle e liberar recursos em `dispose()`;
- funcionar sem qualquer alteração em MainWindow, controllers, Factory,
  Registry ou demais componentes do Host;
- possuir testes de registro, abertura, contribuições, lifecycle e descarte.

`Asset Audit` é a Application de referência desta baseline: coexistindo com
RSC, comprova discovery automático, isolamento de domínio, sessão própria,
lifecycle e contribuições públicas de Menu, Action, View, Toolbar e Dashboard
sem alteração específica no Host.

Uma nova Application não pode:

- modificar o Host para ser reconhecida;
- usar `ProjectSession.rsc_session` ou qualquer bridge do RSC;
- importar classes privadas, controllers, Views ou adaptadores concretos;
- acessar internals de outra Application;
- depender de IDs especiais ou de branches condicionais no Host;
- tratar bridges legadas como contrato de extensão.

## Regra de mudança após a baseline

Qualquer alteração nas APIs estáveis, invariantes, ordem do lifecycle,
responsabilidades do Host ou política de bridges requer avaliação de
compatibilidade, testes de regressão e registro explícito da decisão
arquitetural. Extensões feitas exclusivamente por uma Application não alteram
esta baseline.
