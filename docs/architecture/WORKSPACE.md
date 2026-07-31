# Platform Workspace

## Objetivo

Workspace representa o ambiente físico opcional de um
`platform_sdk.Project`. Ele pertence à infraestrutura e concentra caminhos e
operações simples de diretório sem introduzir filesystem no Aggregate.

## Associação

```text
Workspace ── conhece ──→ Project
Project   ── não conhece ──→ Workspace
```

O caminho é derivado do `aggregate_id`. Revisões do mesmo Project localizam a
mesma raiz física.

## Estrutura

A raiz pode oferecer:

```text
<aggregate_id>/
├── documents/
├── exports/
├── cache/
├── temp/
├── settings/
├── logs/
├── thumbnails/
└── attachments/
```

Nenhum diretório interno é obrigatório. `WorkspaceFactory.create()` cria
somente a raiz. Cada diretório é materializado por `Workspace.ensure()` quando
um consumidor realmente precisar dele.

## API

### Workspace

- mantém Project e raiz física;
- oferece propriedades para todos os caminhos conhecidos;
- cria um diretório interno sob demanda;
- lista somente diretórios existentes;
- permite excluir apenas Workspaces declaradamente temporários.

### WorkspaceFactory

- `create(project)`: cria uma raiz permanente baseada no `aggregate_id`;
- `create_temporary(project)`: cria uma raiz isolada no diretório temporário
  do sistema.

A Factory não cria a árvore completa.

### WorkspaceLocator

- `path_for(project)`: deriva o caminho sem tocar o filesystem;
- `locate(project)`: retorna Workspace quando a raiz já existe;
- nunca cria diretórios.

## Limites

Workspace não:

- persiste o Project;
- interpreta recursos;
- abre documentos;
- executa OCR ou IA;
- acessa Kernel ou RSC;
- mantém cache em memória;
- remove Workspaces permanentes.

Project continua sem importar `pathlib`, `os`, `shutil`, `tempfile` ou qualquer
componente de infraestrutura.

## Ciclo

```text
Project
  ↓ WorkspaceFactory
raiz vazia
  ↓ ensure(diretório)
estrutura parcial sob demanda
  ↓ WorkspaceLocator
reabertura pela mesma identidade
```

Workspaces temporários podem ser excluídos explicitamente. A política de
remoção de Workspaces permanentes fica fora desta versão.
