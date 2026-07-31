# ADR-034 — Presentation Workspace Navigation

**Status:** ACCEPTED
**Data:** 2026-07-31
**Decisores:** Equipe de Arquitetura

## Contexto

O ProcDocOrganizer possui uma arquitetura de apresentação consolidada baseada
em componentes responsáveis por seleção, perspectiva, contexto e montagem do
Workspace. Entre eles destacam-se:

- `NavigationController`;
- `SelectionStore`;
- `PerspectiveStore`;
- `PresentationContextStore`;
- `WorkspaceStore`.

Durante a RFC-001 observou-se que essa infraestrutura já fornece uma fundação
consistente para navegação. Entretanto, ela ainda não representa
explicitamente:

- navegação orientada a recursos do domínio;
- filtros globais de Workspace;
- transições contextuais atômicas;
- navegação profunda (Deep Navigation);
- histórico de contexto;
- independência completa da interface gráfica.

A decisão desta ADR consiste em evoluir essa fundação existente, preservando
sua arquitetura. Não será criado um segundo mecanismo de navegação.

## Decisão

O ProcDocOrganizer adotará um modelo de navegação centralizada, orientada por
intenções e baseada em snapshots imutáveis do contexto de apresentação.

A navegação deixa de ser responsabilidade das Views e passa a ser coordenada
por um Navigation Service. O estado da interface permanece sob
responsabilidade do `PresentationContextStore`.

## Modelo arquitetural

```text
Navigation Intent
        │
        ▼
Navigation Service
        │
        ▼
Presentation Context Store
        │
        ▼
Workspace Snapshot
        │
        ▼
Presentation Adapters
(Qt / Web / CLI)
```

O domínio permanece completamente isolado dessa estrutura.

## Responsabilidades

### Navigation Service

Responsável por:

- receber Navigation Intents;
- validar a navegação;
- produzir novo Workspace Snapshot;
- atualizar contexto;
- atualizar seleção;
- atualizar perspectiva;
- atualizar filtros;
- registrar histórico.

Não é responsável por:

- executar regras normativas;
- consultar Kernel;
- recalcular pontuação;
- acessar entidades de domínio como estado interno.

### PresentationContextStore

Permanece como autoridade sobre o estado da apresentação. Todo estado deverá
ser representado por snapshots imutáveis. Cada alteração produzirá uma nova
revisão do contexto.

### Workspace Snapshot

Representa completamente a sessão de apresentação. Pode conter:

- Project ID;
- Document ID;
- Evidence ID;
- ExecutionFact ID;
- Requirement ID;
- Criterion ID;
- Evaluation ID;
- Perspective;
- Selection;
- Active Filters;
- Revision.

Não contém entidades de domínio. Contém somente identificadores e estado de
apresentação.

### Navigation Intent

Representa uma solicitação de navegação. Cada Intent será imutável, tipada e
independente da interface. Toda Intent poderá conter:

- tipo;
- alvo;
- projeto;
- origem;
- filtros opcionais;
- metadados escalares.

Intents especiais somente deverão existir quando possuírem invariantes
próprias.

## Histórico

O histórico será baseado em Workspace Snapshots. Cada entrada poderá registrar
a Intent recebida e o Snapshot produzido. O Snapshot será considerado a
autoridade para restauração da navegação.

## Workspace Filters

Filtros pertencem ao Workspace Context. Não pertencem às Views nem ao
Navigation Service. O Navigation Service apenas coordena sua aplicação.

## Deep Navigation

Todo recurso apresentado ao usuário deverá permitir navegação direta para
recursos relacionados:

```text
Document
↓
Evidence
↓
ExecutionFact
↓
Criterion
↓
Requirement
↓
Evaluation
↓
Report
```

Também deverá existir navegação inversa. A implementação concreta será
incremental.

## Desacoplamento

As Views:

- não conhecem outras Views;
- não alteram diretamente o contexto;
- não controlam histórico;
- não executam navegação.

Os ViewModels:

- emitem Navigation Intents;
- recebem projeções do Workspace.

Nenhum ViewModel referencia outro ViewModel.

## Independência de Plataforma

O modelo deverá permanecer compatível com Desktop (Qt), Web e CLI. A
plataforma é responsabilidade exclusiva dos adaptadores de apresentação.

## Consequências

Benefícios esperados:

- menor acoplamento;
- navegação consistente;
- Deep Navigation;
- histórico;
- favoritos futuros;
- restauração de sessão;
- facilidade para futura interface Web.

Custos:

- maior disciplina arquitetural;
- centralização das transições;
- necessidade de contratos claros entre Presentation e Navigation.

## Não Objetivos

Esta ADR não introduz:

- múltiplos Workspaces;
- sincronização entre sessões;
- colaboração em tempo real;
- interface Web;
- novos recursos funcionais.

Esses temas poderão ser tratados em ADRs futuras.

## Relação com princípios existentes

Esta decisão preserva:

- P-001 — Progressive Evaluation;
- `PRODUCT_VISION`;
- Architecture Overview;
- Workspace Dashboard;
- Evaluation Report.

Não altera Core, Kernel, Pipeline, persistência ou domínio normativo.

## Decisão Final

A arquitetura existente de apresentação será preservada e evoluída.

`NavigationController`, `SelectionStore`, `PerspectiveStore`,
`PresentationContextStore` e `WorkspaceStore` permanecem válidos.

O novo Navigation Service atuará como coordenador das intenções e transições.
O `PresentationContextStore` continuará sendo a autoridade sobre o estado da
interface, representado por snapshots imutáveis.

Nenhum mecanismo paralelo de navegação será criado.
