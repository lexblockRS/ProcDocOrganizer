# FS-001 – Criar Projeto

## Objetivo

Criar um novo projeto ProcDocOrganizer (.pdop), inicializando toda a estrutura necessária para armazenamento de dados, configurações e arquivos gerados durante o trabalho.

---

## Descrição

Um projeto representa um conjunto independente de documentos, evidências e classificações.

Cada projeto é armazenado em uma pasta com extensão ".pdop".

O ProcDocOrganizer poderá trabalhar com apenas um projeto aberto por vez.

---

## Fluxo Principal

1. O usuário seleciona **Arquivo → Novo Projeto**.

2. O sistema solicita:

   - Nome do projeto;
   - Pasta onde será criado.

3. O usuário confirma.

4. O sistema verifica:

   - se a pasta existe;
   - se já existe um projeto com o mesmo nome.

5. Caso não exista:

   - cria a estrutura do projeto;
   - cria o banco de dados;
   - grava os arquivos iniciais;
   - abre automaticamente o projeto.

---

## Estrutura criada

Projeto.pdop/

    database.db

    project.json

    cache/

    exports/

    logs/

    temp/

---

## project.json

O arquivo project.json contém apenas informações gerais do projeto.

Exemplo:

{
    "name": "RSC Alexander",
    "version": 1,
    "created_at": "...",
    "last_opened_at": "...",
    "database": "database.db"
}

---

## Banco de Dados

Na criação do projeto será gerado um banco SQLite vazio.

As tabelas serão criadas automaticamente pelo sistema.

---

## Regras de Negócio

RN-001

O nome do projeto não pode ser vazio.

RN-002

Não pode existir outro projeto com o mesmo nome na pasta escolhida.

RN-003

O sistema nunca altera projetos existentes sem confirmação do usuário.

RN-004

A abertura do projeto ocorre automaticamente após sua criação.

RN-005

Somente um projeto poderá permanecer aberto por vez.

---

## Tratamento de Erros

Caso a pasta não possa ser criada:

Exibir mensagem de erro.

Caso não exista permissão de escrita:

Cancelar a operação.

Caso ocorra erro durante a criação:

Remover arquivos parcialmente criados.

---

## Resultado Esperado

Ao final da operação:

- projeto criado;
- banco criado;
- estrutura inicial criada;
- projeto aberto;
- interface preparada para utilização.