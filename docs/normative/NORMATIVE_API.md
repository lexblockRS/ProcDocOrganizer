# API conceitual do Modelo Normativo RSC-PCCTAE

## 1. Objetivo

A API conceitual oferece uma visão de consulta do Decreto nº 13.048/2026 sem
expor aos consumidores a divisão física entre os seis arquivos documentais.
Ela não avalia requerimentos, não calcula pontos e não enquadra atividades.

O Decreto permanece a fonte de verdade. A API apenas projeta registros
imutáveis derivados de:

- `decree_articles.json`;
- `decree_requirements.json`;
- `decree_criteria.json`;
- `decree_tables.json`;
- `decree_documents.json`;
- `decree_traceability.json`.

## 2. Fachada pública

O contrato público recebe o nome `Decree13048NormativeModel`. A identificação
do decreto no nome evita que a futura inclusão de outra norma transforme uma
API específica em uma abstração falsamente genérica.

```text
Decree13048NormativeModel
├── RscRequirementView
├── RscCriterionView
├── RscAnnexTableView
├── AcceptedDocumentView
├── LegalProvisionView
└── LegalTraceabilityView
```

Todas as Views são projeções somente leitura. “View” significa uma forma
conceitual de consulta, não DTO Python nem componente visual.

## 3. Localização dos objetos

### Requisito

`findRequirement(requirementId)` localiza exclusivamente por ID estável, como
`DEC13048-ART3-I`. O retorno contém o texto do inciso, o Anexo relacionado, a
tabela e a origem jurídica.

### Critério

`findCriterion(criterionId)` localiza exclusivamente por ID estável, como
`DEC13048-ANX-II-ITEM-04`. Unidade e pontos são retornados como texto literal.
No Anexo V, as variantes titular e substituto permanecem separadas.

### Critérios de um requisito

`criteriaOfRequirement(requirementId)` percorre somente relações explícitas:

```text
Requirement.annex
        ↓
RscAnnexTableView.criterionIds
        ↓
RscCriterionView
```

A ordem normativa dos itens é preservada. Não há filtragem por caso concreto.

### Tabela

`tableOfRequirement(requirementId)` retorna a tabela indicada pelo requisito.
`tableOfCriterion(criterionId)` usa o campo `table` do critério. Ambas devem
produzir a mesma tabela para registros consistentes.

### Documentos aceitos

`acceptedDocuments()` retorna as dez categorias expressamente extraídas do
art. 4º, parágrafo único. O inciso VII permanece aberto nos exatos limites do
texto: a API não inventa os documentos de futuro ato ministerial.

### Origem jurídica

`traceability(objectId)` retorna a origem do registro e sua posição jurídica.
`relatedArticles(objectId)` retorna somente artigos ligados por referência
estruturada. Texto semelhante não cria relação.

### Restrições e observações

`restrictions(reference)` retorna disposições jurídicas previamente
estruturadas para a referência. Como os arquivos de entrada não possuem uma
coleção autônoma de restrições, a operação não interpreta linguagem natural:
ela devolve `LegalProvisionView` ou coleção vazia.

`observations(objectId)` expõe literalmente o campo `notes`. `null` significa
ausência de observação estruturada, não ausência de efeitos jurídicos.

## 4. Tratamento de ausência

Operações `find*` retornam “não encontrado” de forma explícita, sem criar
objetos parciais. Operações plurais retornam coleção vazia quando não há
relação estruturada. Um registro com `null` preserva o desconhecido como
desconhecido.

## 5. Dependências documentais

| Projeção | Fonte primária | Relações utilizadas |
|---|---|---|
| `RscRequirementView` | `decree_requirements.json` | `annex`, `table` |
| `RscCriterionView` | `decree_criteria.json` | `inciso`, `annex`, `table` |
| `RscAnnexTableView` | `decree_tables.json` | `criterion_ids` |
| `AcceptedDocumentView` | `decree_documents.json` | posição do art. 4º |
| `LegalProvisionView` | `decree_articles.json` | posição do artigo |
| `LegalTraceabilityView` | `decree_traceability.json` | datasets e referências |

## 6. Invariantes

1. O modelo e todas as Views são somente leitura.
2. Nenhuma norma pode ser alterada em tempo de execução.
3. IDs são imutáveis, únicos e comparados integralmente.
4. Todo objeto retornado possui `documentId`, `officialText`,
   `legalReference`, `hierarchy` e `effectiveFrom`.
5. Toda relação deve existir nos JSON; similaridade textual não é relação.
6. A ordem dos critérios é a ordem dos itens do Anexo.
7. Valores normativos permanecem textuais; a API não os converte para cálculo.
8. `null` nunca é preenchido por inferência.
9. Não pode haver duplicidade de requisito, critério, tabela ou documento.
10. Falha de integridade impede a disponibilização do modelo completo.

## 7. Fora do escopo

Não pertencem a esta API:

- avaliação ou enquadramento de Activity;
- cálculo, soma, saldo ou comparação de pontuação;
- decisão sobre sobreposição;
- interpretação de conceitos qualitativos;
- classificação de documentos apresentados;
- persistência de casos concretos;
- alteração ou complementação da norma.
