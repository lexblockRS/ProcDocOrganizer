# ADR-035 — Resource Presentation Model

**Status:** ACCEPTED
**Data:** 2026-07-31
**Decisores:** Equipe de Arquitetura

**Relacionada a:**

- `PRODUCT_VISION`;
- ADR-034 — Presentation Workspace Navigation;
- RFC-002 — Resource Presentation Model.

## Contexto

Após a consolidação do Presentation Workspace verificou-se que diversos
elementos da interface compartilham comportamento semelhante de navegação:

- Document;
- Evidence;
- ExecutionFact;
- Requirement;
- Criterion;
- Evaluation;
- Report.

Esses elementos pertencem ao domínio, mas a camada de apresentação necessita
apenas de uma representação reduzida, navegável e independente de toolkit.

A RFC-002 concluiu que a criação de uma abstração de apresentação é desejável,
desde que ela não replique o domínio.

## Decisão

Adotar Resource como DTO imutável da camada de apresentação.

Resource representa exclusivamente uma projeção navegável. Não representa uma
entidade de domínio, não substitui o domínio e não encapsula comportamento.

## Estrutura

Todo Resource deverá conter apenas:

- ResourceIdentity;
- Display;
- Relationships;
- AvailableActions.

Nenhuma informação adicional será obrigatória.

## ResourceIdentity

Identity representa:

- ResourceType;
- ResourceId.

A identidade é estável. DisplayName, Status e Metadata não pertencem à
identidade.

## Display

Display poderá conter:

- DisplayName;
- Status;
- Metadata escalar.

Esses campos destinam-se exclusivamente à apresentação. Nenhum deles poderá
ser utilizado para decisões normativas.

## Relationships

Relacionamentos serão representados apenas por identidades. Cada
relacionamento conterá:

- RelationshipType;
- Target ResourceIdentity;
- Label opcional;
- Metadata escalar opcional.

Nunca conterá outro Resource ou entidade de domínio.

### Relationship Types

Inicialmente:

- `USED_BY`;
- `CONTAINS`;
- `PRODUCES`;
- `BELONGS_TO`;
- `REFERENCES`;
- `DEPENDS_ON`.

Novos tipos dependerão de evolução arquitetural explícita.

## Available Actions

Resources declaram apenas ações disponíveis e nunca as executam. As ações
serão representadas por tipos, inicialmente:

- `OPEN`;
- `INSPECT`;
- `REVEAL`;
- `COPY_IDENTIFIER`.

Toda ação que alterar estado deverá produzir uma Intent apropriada.

## Projection Services

Resources serão produzidos por Projection Services. Cada tipo possuirá seu
próprio projetor, como:

- DocumentResourceProjector;
- EvidenceResourceProjector;
- RequirementResourceProjector.

Nenhum projetor deverá conhecer Views ou toolkit. Projection Services apenas
traduzem: nunca enriquecem, interpretam ou recalculam o domínio.

## Workspace

Workspace Snapshot continuará armazenando apenas identidades. Nunca armazenará
Resources completos.

O fluxo oficial é:

```text
ResourceIdentity
       ↓
Navigation Intent
       ↓
Navigation Service
       ↓
Workspace Snapshot
       ↓
Projection Service
       ↓
Resource
       ↓
Presentation
```

## Resource Collections

Coleções de Resources não constituem novos Resources. Quando necessário,
utilizar:

```text
ResourceCollection
       ↓
Resources
       ↓
Total
       ↓
Projection Context
```

Coleções representam resultados de consulta.

## Metadata

Metadata deverá permanecer imutável, escalar e orientada exclusivamente à
apresentação. Não poderá substituir contratos formais. Campos recorrentes
deverão evoluir para atributos explícitos.

## Restrições

Resources:

- não executam regras;
- não executam persistência;
- não consultam SQLite;
- não modificam domínio;
- não possuem entidades;
- não possuem comportamento normativo.

## Compatibilidade

O modelo permanece compatível com Qt, Web e CLI, sem dependências específicas
de plataforma.

## Princípios derivados

### P-003 — Everything Visible Is a Resource

Todo elemento navegável apresentado ao usuário deverá possuir uma projeção
Resource.

### P-004 — Projection Neutrality

Projection Services apenas traduzem informações para apresentação. Nunca
alteram significado do domínio.

## Consequências

Benefícios:

- Inspector único;
- baixo acoplamento;
- navegação uniforme;
- reutilização;
- compatibilidade futura com Web;
- projeções pequenas;
- domínio preservado.

Custos:

- necessidade de projetores específicos;
- disciplina na evolução das projeções.

## Não objetivos

Esta ADR não introduz:

- Inspector;
- Coverage Analyzer;
- Timeline Explorer;
- novos componentes do domínio;
- novas regras de negócio.

Ela apenas estabelece o modelo oficial de Resource da camada de apresentação.

## Decisão Final

Resource passa a ser a única representação navegável da camada de
apresentação. Ele permanece pequeno, imutável, desacoplado do domínio e
produzido exclusivamente por Projection Services especializados.

O domínio continua sendo a única autoridade sobre regras de negócio. A
apresentação continua sendo apenas uma projeção desse domínio.
