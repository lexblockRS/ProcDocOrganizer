# Platform Project Model

## Objetivo

`platform_sdk.Project` é o Aggregate Root genérico que representa qualquer
projeto hospedado pelo ProcDocOrganizer. Ele define identidade, aplicação
proprietária, metadados, estado, recursos e ciclo de vida sem conhecer nenhum
domínio de aplicação.

O modelo histórico `models.Project` permanece temporariamente responsável
pela compatibilidade do formato físico atual. Esta sprint não migra Host nem
aplicações existentes. A adoção do novo Aggregate será explícita e gradual.

## Modelo

```text
Project
├── project_id / aggregate_id
├── name
├── application_id
├── metadata
├── state
├── resources: ProjectResource[]
└── revision
```

### Identidade

`project_id` é um UUID estável. `aggregate_id` expõe essa identidade e
`same_project(other)` compara duas representações do mesmo Project.

A igualdade e o hash do Aggregate usam exclusivamente a identidade. Mudanças
de nome, estado, metadados ou recursos não criam um novo projeto.

### Aplicação proprietária

`application_id` é obrigatório e opaco. O Project não importa descriptor,
registry ou implementação concreta. A associação não transfere lógica de
negócio para a plataforma.

### Metadados

Metadados são pares imutáveis de chave e valor escalar. Não admitem chaves
duplicadas nem objetos executáveis.

### Recursos

`ProjectResource` é uma referência opaca, identificada e tipada. O Aggregate
controla associação e remoção, mas não abre arquivos, bancos, serviços ou
objetos pertencentes à aplicação.

## Ciclo de vida

```text
DRAFT ─────→ ACTIVE ─────→ SUSPENDED
  │            │              │
  │            └──────┐       └──→ ACTIVE
  └───────────────────┴──────────→ ARCHIVED
```

`ARCHIVED` é terminal. Renomeação e alteração de recursos são proibidas
depois do arquivamento. Operações efetivas incrementam `revision`; operações
redundantes preservam a instância.

## Imutabilidade

Project e ProjectResource são dataclasses congelados. Renomeação, mudança de
estado e associação de recursos retornam novos snapshots. A identidade e a
aplicação proprietária são preservadas.

## Limites arquiteturais

Project não conhece:

- RSC, Criterion ou Kernel;
- OCR ou IA;
- SQLite ou outro banco;
- filesystem ou formato de container;
- UI ou Host;
- implementação da aplicação proprietária.

Persistência, timestamps, histórico de revisões e materialização de recursos
pertencem a camadas externas.

## Migração futura

Antes de substituir `models.Project`, será necessário:

1. criar um adapter entre o formato histórico e o novo Aggregate;
2. definir persistência de identidade e revisão;
3. migrar ProjectManager e sessões sem quebrar projetos existentes;
4. separar definitivamente Aggregate e representação física;
5. manter ApplicationRegistry dependente apenas de uma projeção neutra.
