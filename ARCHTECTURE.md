# ProcDocOrganizer - Arquitetura do Sistema

## 1. Objetivo

O ProcDocOrganizer é uma aplicação desktop destinada à organização de evidências documentais para instrução de processos administrativos.

A primeira aplicação será o apoio à montagem de processos de Reconhecimento de Saberes e Competências (RSC), porém sua arquitetura deverá permitir utilização em outros processos administrativos.

O software não toma decisões pelo usuário.

Sua função é localizar documentos, organizar evidências e apresentar as informações de forma estruturada.

---

# 2. Princípios

O desenvolvimento seguirá os seguintes princípios.

- Funcionamento totalmente offline.
- Nunca modificar documentos originais.
- Toda evidência deve possuir um documento de origem.
- O usuário é responsável pela criação e validação das evidências.
- O sistema apenas organiza e apresenta as informações.
- Toda pontuação deve ser reproduzível e auditável.
- Interface simples e objetiva.
- Código modular e de fácil manutenção.

---

# 3. Conceitos

## Projeto

Representa um trabalho em andamento.

Um projeto contém:

- documentos
- evidências
- configurações

---

## Documento

É um arquivo utilizado como fonte de informação.

Exemplos:

- PDF
- Portaria
- Certificado
- Boletim

O documento nunca será alterado.

---

## Evidência

É uma informação comprovada por um documento.

Uma evidência poderá conter:

- título
- descrição
- data
- período
- observações
- documento de origem
- classificação RSC

Um documento poderá gerar várias evidências.

---

## Critério RSC

Representa um item previsto na regulamentação do RSC.

O usuário escolhe o critério.

O sistema calcula automaticamente a pontuação correspondente.

---

# 4. Fluxo

Projeto

↓

Importar documentos

↓

Localizar documentos do servidor

↓

Criar evidências

↓

Linha do Tempo (automática)

↓

Classificar evidências no RSC

↓

Calcular pontuação

↓

Exportar processo

---

# 5. Visualizações

O sistema gera automaticamente diferentes formas de visualizar os mesmos dados.

## Linha do Tempo

Organiza cronologicamente todas as evidências.

Não é cadastrada pelo usuário.

É construída automaticamente.

## Pontuação

Resume a pontuação obtida em cada requisito do RSC.

## Relatórios

Permitem exportação para Excel, PDF e outros formatos.

---

# 6. Arquitetura Geral

Projeto

├── Documentos

├── Evidências

├── Critérios RSC

└── Visualizações

        ├── Linha do Tempo

        ├── Pontuação

        └── Relatórios

---

# 7. Evolução

A arquitetura deverá permitir futuras funcionalidades sem alterar seus princípios fundamentais.

Exemplos futuros:

- IA para auxiliar identificação de evidências.
- IA para apoio à elaboração do memorial.
- Outros processos administrativos além do RSC.

Essas funcionalidades serão opcionais e não farão parte da versão inicial.