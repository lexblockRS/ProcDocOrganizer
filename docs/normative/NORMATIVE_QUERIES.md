# Catálogo de consultas normativas

## 1. Regras gerais

As consultas são determinísticas, somente leitura e baseadas em igualdade de
IDs ou em relações explícitas. Não existe busca por “melhor critério”,
pontuação suficiente, similaridade semântica ou adequação de Activity.

## 2. Consultas fundamentais

### `findRequirement(requirementId)`

1. Recebe um ID completo.
2. Consulta a coleção `requirements`.
3. Retorna uma única `RscRequirementView`.
4. Não aceita inciso isolado como substituto silencioso do ID.

Exemplo conceitual:

```text
findRequirement("DEC13048-ART3-IV")
→ requisito do art. 3º, inciso IV
```

### `findCriterion(criterionId)`

Consulta `criteria` pelo ID integral e preserva texto, unidade, pontos e
variantes sem conversão.

### `criteriaOfRequirement(requirementId)`

1. Localiza o requisito.
2. Localiza sua tabela pelo `table`.
3. Resolve cada valor de `criterion_ids`.
4. Confirma `annex`, `table` e `inciso`.
5. Retorna os critérios na ordem normativa.

Qualquer referência quebrada é erro de integridade, não item a ser ignorado.

### `findTable(tableId)`

Retorna uma única `RscAnnexTableView` por ID estável.

### `tableOfRequirement(requirementId)`

Resolve o campo `table` do requisito e confirma que o inciso e o Anexo
coincidem.

### `tableOfCriterion(criterionId)`

Resolve o campo `table` do critério e confirma que seu ID aparece em
`criterionIds`.

## 3. Documentos

### `acceptedDocuments()`

Retorna todos os `AcceptedDocumentView` na ordem do art. 4º. As alíneas do
inciso III são itens independentes porque assim foram estruturadas na entrada.

### `findAcceptedDocument(documentTypeId)`

Localiza uma categoria documental normativa. Não localiza arquivo físico e não
valida comprovação.

## 4. Rastreabilidade

### `traceability(objectId)`

Produz `LegalTraceabilityView` usando os campos de origem do próprio objeto.
Para o documento raiz e os índices de datasets, usa
`decree_traceability.json`.

### `relatedArticles(objectId)`

Retorna artigos cuja relação seja explícita na posição jurídica ou nas
referências cruzadas. Para requisitos e critérios, o art. 3º é a ligação
estruturada disponível. Para documentos aceitos, o art. 4º é a ligação
estruturada.

Não são inferidas referências a partir de palavras presentes no texto.

## 5. Restrições

### `restrictions(reference)`

Finalidade: permitir que um consumidor encontre disposições potencialmente
limitadoras já estruturadas, sem transformar seu conteúdo em predicado.

Contrato:

- recebe ID ou referência jurídica estruturada;
- retorna `LegalProvisionView`;
- preserva o texto integral;
- não responde se a restrição foi satisfeita;
- não extrai automaticamente proibições do texto;
- retorna vazio quando a entrada não contém vínculo estruturado.

Consequentemente, a API atual permite consultar as disposições dos artigos,
mas não promete um catálogo exaustivo de restrições. Essa limitação reflete as
entradas, que não possuem coleção `restrictions`.

## 6. Observações

### `observations(objectId)`

Retorna literalmente `notes`. Não sintetiza comentários a partir de outros
campos. `null` é um resultado válido.

## 7. Consultas deliberadamente ausentes

- `calculatePoints`;
- `evaluate`;
- `rank`;
- `matchActivity`;
- `criterionResult`;
- `requirementResult`;
- `isEligible`;
- `bestCriterion`;
- `consumeBalance`.

Essas operações exigiriam interpretação ou execução normativa e estão fora
deste contrato.
