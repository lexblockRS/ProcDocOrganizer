# Contratos conceituais do Modelo Normativo

## 1. Convenções

Os contratos abaixo descrevem dados e pré/pós-condições. Não especificam
linguagem, framework, DTO, Repository ou Service. Coleções são ordenadas e
imutáveis. Campos opcionais preservam `null`.

## 2. `Decree13048NormativeModel`

Responsabilidade: fornecer o único ponto público de consulta aos seis conjuntos
documentais.

Estado conceitual:

| Campo | Tipo conceitual | Regra |
|---|---|---|
| `documentId` | texto | sempre `BR-DEC-13048-2026` |
| `schema` | texto | versão documental das entradas |
| `effectiveFrom` | data textual | preservada da fonte |
| `sourceUrl` | texto | URL oficial registrada |

Não expõe mutadores, recarga parcial nem substituição de coleções.

## 3. `RscRequirementView`

Representa um dos seis incisos do art. 3º.

Campos:

- `id`;
- `inciso`;
- `annexId`;
- `tableId`;
- `officialText`;
- `legalReference`;
- `hierarchy`;
- `effectiveFrom`;
- `notes`.

Invariantes: `inciso`, `annexId` e `tableId` existem; a associação é
unívoca; o ID coincide com a posição jurídica.

## 4. `RscCriterionView`

Representa um item de uma tabela dos Anexos I a VI.

Campos:

- `id`;
- `requirementInciso`;
- `annexId`;
- `tableId`;
- `item`;
- `officialText`;
- `unit`;
- `pointsText`;
- `variants`;
- dados comuns de rastreabilidade.

`pointsText` preserva o valor oficial. `variants` é `null` fora do Anexo V e
preserva os pares papel/valor quando presentes. O contrato não fornece total,
peso convertido ou resultado.

## 5. `RscAnnexTableView`

Representa uma das seis tabelas.

Campos:

- `id`;
- `annexId`;
- `requirementInciso`;
- `officialHeading`;
- `columns`;
- `criterionIds`;
- dados comuns de rastreabilidade.

`criterionIds` não contém duplicidade e preserva a ordem dos itens.

## 6. `AcceptedDocumentView`

Representa uma categoria documental expressamente enumerada no art. 4º,
parágrafo único.

Campos:

- `id`;
- `inciso`;
- `subitem`;
- `officialText`;
- dados comuns de rastreabilidade.

O contrato não afirma que um documento real satisfaz a categoria e não amplia
o inciso VII.

## 7. `LegalProvisionView`

Representa texto de artigo disponibilizado para consulta.

Campos:

- `id`;
- `article`;
- `officialText`;
- `legalReference`;
- `hierarchy`;
- `effectiveFrom`;
- `notes`.

O texto agregado de um artigo não é decomposto pela API em regras executáveis.

## 8. `LegalTraceabilityView`

Representa a origem de um objeto normativo.

Campos:

- `objectId`;
- `documentId`;
- `article`;
- `paragraph`;
- `inciso`;
- `annex`;
- `table`;
- `item`;
- `officialText`;
- `legalReference`;
- `hierarchy`;
- `effectiveFrom`;
- `notes`.

Todos os demais contratos devem poder produzir esta projeção.

## 9. Contratos das operações

| Operação | Entrada | Saída | Ausência |
|---|---|---|---|
| `findRequirement` | ID de requisito | requisito único | não encontrado |
| `findCriterion` | ID de critério | critério único | não encontrado |
| `criteriaOfRequirement` | ID de requisito | critérios ordenados | requisito inválido: não encontrado |
| `findTable` | ID de tabela | tabela única | não encontrado |
| `tableOfRequirement` | ID de requisito | tabela única | relação inválida |
| `tableOfCriterion` | ID de critério | tabela única | relação inválida |
| `acceptedDocuments` | nenhuma | documentos ordenados | coleção vazia |
| `findAcceptedDocument` | ID documental | documento único | não encontrado |
| `traceability` | ID conhecido | origem única | não encontrado |
| `relatedArticles` | ID conhecido | artigos relacionados | coleção vazia |
| `restrictions` | referência estruturada | disposições relacionadas | coleção vazia |
| `observations` | ID conhecido | texto de `notes` ou `null` | não encontrado |

## 10. Falhas conceituais

- `UnknownNormativeId`: ID não pertence ao modelo.
- `DuplicateNormativeId`: ID repetido.
- `BrokenNormativeReference`: relação aponta para objeto ausente.
- `NormativeDocumentMismatch`: objetos apresentam `document_id` divergente.
- `IncompleteTraceability`: campo obrigatório de origem está ausente.
- `UnsupportedNormativeSchema`: schema documental não reconhecido.

Esses nomes descrevem condições do contrato; não constituem classes
implementadas.
