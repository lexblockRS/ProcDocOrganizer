# Migration Guide

## Autoridade única

`database/migrations.py` é a única autoridade para criar ou evoluir o schema
SQLite. `PRAGMA user_version` identifica a versão física suportada e cada nova
evolução deve ser adicionada como migration sequencial em
`database/schema.py` e aplicada pelo Migration Manager.

Stores não executam `CREATE TABLE`, `ALTER TABLE` ou mudanças de versão. Ao
abrir um banco, eles solicitam sua inicialização pelo fluxo oficial e depois
executam somente operações de persistência.

## Migration V8

A V8 incorporou ao fluxo oficial as tabelas:

- `platform_projects`;
- `platform_evidences`;
- `platform_documents`;
- `platform_evidence_documents`;
- `platform_execution_facts`;
- `platform_execution_bindings`.

As declarações usam `IF NOT EXISTS` para reconhecer bancos Alpha nos quais os
Stores antigos já haviam criado essas tabelas. Assim, a adoção da autoridade
única preserva os dados existentes.

## Procedimento para evoluções futuras

1. incrementar `SUPPORTED_SCHEMA_VERSION`;
2. declarar os comandos da nova migration em `database/schema.py`;
3. criar a função `_apply_migration_vN`;
4. atualizar `PRAGMA user_version` e `index_state.schema_version`;
5. testar banco novo, upgrade da versão anterior e rollback em falha;
6. nunca duplicar DDL em Store, repository ou UI.
