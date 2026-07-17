# Modelo de Dados

## Objetivo

Este documento descreve as entidades utilizadas pelo ProcDocOrganizer e os relacionamentos entre elas.

O objetivo é manter uma estrutura simples, flexível e independente de um processo administrativo específico.

---

# Entidades

## Projeto

Representa um trabalho realizado pelo usuário.

Um projeto possui:

- documentos;
- evidências;
- configurações.

---

## Documento

Representa um arquivo utilizado como fonte de informação.

Exemplos:

- Portaria
- Certificado
- Boletim
- Processo
- Declaração

Cada documento possui:

- nome;
- caminho;
- hash;
- número de páginas;
- texto extraído;
- data do documento;
- observações.

Um documento poderá gerar nenhuma, uma ou várias evidências.

---

## Evidência

Representa um fato comprovado por um documento.

Exemplos:

- Participação em comissão;
- Exercício de chefia;
- Curso de capacitação;
- Fiscalização de contrato;
- Publicação;
- Projeto de extensão.

Cada evidência possui:

- título;
- descrição;
- categoria;
- data inicial;
- data final (opcional);
- observações;
- documento de origem.

Uma evidência poderá ser classificada em um critério do RSC.

---

## Critério RSC

Representa um item previsto na regulamentação.

Cada critério possui:

- código;
- descrição;
- requisito;
- pontuação.

Esses dados serão importados da tabela de critérios do RSC.

---

# Relacionamentos

Projeto

↓

Documentos

↓

Evidências

↓

Critério RSC

---

# Visualizações

As informações cadastradas poderão ser apresentadas através de:

- Linha do Tempo;
- Pontuação;
- Relatórios.

Essas visualizações não armazenam dados próprios.

São geradas automaticamente pelo sistema.