# Resource Infrastructure

**Release:** Beta 1.1
**Base:** ADR-035 — Resource Presentation Model

## Objetivo

A infraestrutura de Resource oferece uma representação navegável, pequena e
imutável para a camada de apresentação. Resource não é domínio, Aggregate,
persistência, View ou ViewModel.

```text
ResourceIdentity
       ↓
ProjectionService.project(identity, workspace_snapshot)
       ↓
Resource
       ↓
Presentation Adapter futuro
```

Nenhum Inspector ou componente visual é introduzido nesta infraestrutura.

## ResourceIdentity

`ResourceIdentity` contém exclusivamente `ResourceType` e `resource_id`.
DisplayName, Status e Metadata não participam da identidade. Os tipos iniciais
são Document, Evidence, ExecutionFact, Requirement, Criterion, Evaluation e
Report.

## Resource e Display

`Resource` é um DTO frozen e slotted composto por:

- `identity`;
- `display`;
- `relationships`;
- `available_actions`.

`ResourceDisplay` separa nome, status e metadata da identidade. Metadata é
copiada e congelada, aceita somente valores escalares e possui finalidade
exclusiva de apresentação.

## Relationships

`ResourceRelationship` contém tipo, identidade de destino, label opcional e
metadata escalar. O destino nunca é outro Resource nem uma entidade.

Tipos iniciais:

- `USED_BY`;
- `CONTAINS`;
- `PRODUCES`;
- `BELONGS_TO`;
- `REFERENCES`;
- `DEPENDS_ON`.

## Actions

`PresentationAction` declara `OPEN`, `INSPECT`, `REVEAL` e
`COPY_IDENTIFIER`. Esses valores não possuem callbacks nem executam operações.
Uma futura ação que altere o estado deverá produzir uma Navigation Intent.

## ResourceCollection

`ResourceCollection` representa um resultado de consulta. Contém uma tupla de
Resources, o total do resultado e um contexto escalar da projeção. A coleção
não é Resource, Aggregate ou modelo persistente.

## Projection Services

`ProjectionService` é o contrato independente de toolkit:

```text
project(ResourceIdentity, WorkspaceSnapshot) → Resource
```

Os projetores iniciais são:

- `DocumentResourceProjector`;
- `EvidenceResourceProjector`;
- `RequirementResourceProjector`.

Nesta fundação eles produzem a menor projeção neutra possível: preservam a
identidade, usam seu identificador como apresentação provisória e declaram
somente a ação `OPEN`. Não consultam entidades, serviços de negócio, Kernel,
banco ou Views. Nomes e estados adicionais somente poderão ser traduzidos de
fontes explícitas em sprints futuras, sem interpretação, inferência ou
ampliação da responsabilidade desses contratos.

## Serialização

As funções `serialize_resource` e `serialize_resource_collection` convertem os
DTOs em estruturas compostas apenas por valores simples. A serialização não
reidrata entidades e não modifica significado.

## Fronteiras

Os módulos de Resource podem depender apenas de contratos de apresentação e da
biblioteca padrão. São proibidas dependências de Qt, Web, CLI, domínio,
persistência, SQLite, Kernel ou Pipeline.

O Workspace Snapshot continua armazenando apenas identidades e estado de
navegação. Resources completos não são incorporados ao Workspace.
