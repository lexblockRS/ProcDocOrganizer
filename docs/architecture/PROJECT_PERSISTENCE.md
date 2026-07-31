# Project Persistence V1

## Objetivo

`SQLiteProjectStore` demonstra que o Aggregate `platform_sdk.Project` pode ser
salvo, fechado e reaberto sem perda de identidade, revisão ou estado.

A persistência é um adapter simples. O domínio não foi alterado e não conhece
SQLite.

## Modelo físico

Uma única tabela é utilizada:

```sql
platform_projects
├── project_id TEXT PRIMARY KEY
├── name TEXT NOT NULL
├── application_id TEXT NOT NULL
├── metadata_json TEXT NOT NULL
├── state TEXT NOT NULL
├── resources_json TEXT NOT NULL
└── revision INTEGER NOT NULL
```

Não existem tabelas de ExecutionFact, CriterionScore, RequirementScore,
RSCProcess ou Evidence nesta versão.

## Identidade

`project_id` é a chave primária e corresponde ao `aggregate_id`. Um `save` de
uma revisão do mesmo Project atualiza a linha existente. Projects diferentes
ocupam linhas independentes.

Ao reabrir, o UUID é entregue novamente ao construtor do Aggregate, sem gerar
uma nova identidade.

## Revisões

O campo `revision` é persistido como inteiro não negativo. O Store não cria,
incrementa ou interpreta revisões; ele apenas preserva o snapshot recebido.

Não há histórico de revisões nesta V1. Salvar nova revisão substitui o
snapshot corrente do mesmo `aggregate_id`.

## Metadados e recursos

Metadados e `ProjectResource` são serializados explicitamente como JSON dentro
de colunas textuais. Na leitura, são reconstruídos como tuplas e Value Objects
imutáveis.

As referências de recursos continuam opacas. O Store não abre arquivos nem
interpreta seu conteúdo.

## Operações

- `save(project)`: insere ou substitui o snapshot corrente;
- `get(project_id)`: reidrata um Aggregate;
- `list_all()`: lista Projects ordenados por identidade;
- `close()`: encerra a conexão;
- context manager: garante fechamento ao final do bloco.

Project inexistente produz `ProjectNotFoundError`.

## Estratégia

A implementação utiliza `sqlite3` diretamente e uma transação por `save`.
Não há:

- cache;
- ORM;
- Unit of Work;
- repository genérico;
- lazy loading;
- migração de objetos RSC;
- otimização prematura.

## Limitações

- mantém apenas o snapshot mais recente;
- não possui concorrência otimista;
- não mantém auditoria de alterações;
- não define migração de schema;
- não integra o Host ou o modelo físico legado;
- não persiste o processo RSC.

Essas limitações são intencionais para validar a persistibilidade do modelo
atual sem antecipar arquitetura adicional.
