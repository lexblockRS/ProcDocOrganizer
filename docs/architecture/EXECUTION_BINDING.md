# Execution Binding

## Separação de responsabilidades

O fluxo passa a distinguir explicitamente quatro conceitos:

```text
ExecutionFact
    ↓
ExecutionBinding
    ↓
Contrato normativo
    ↓
CriterionScoringKernel
```

`ExecutionFact` permanece um fato observável e neutro. `ExecutionBinding`
registra a decisão de enquadrar esse fato em uma definição já existente no
catálogo. O contrato normativo será resolvido posteriormente, e somente o
Kernel poderá executar a aritmética correspondente.

## Modelo

Um Binding possui identidade própria, referência ao ExecutionFact, os
identificadores de Criterion, Requirement e Execution Rule, origem, data de
criação e metadados opcionais. Ele não contém quantidade, período, documento,
valor normativo, cálculo ou pontuação.

A origem suportada nesta versão é `MANUAL`. O enum poderá receber futuramente
origens como OCR, IA, importação ou migração sem modificar o significado dos
Bindings existentes.

Cada ExecutionFact possui no máximo um Binding ativo. Alterar o enquadramento
preserva `binding_id`, `execution_fact_id`, origem e data de criação. O
ExecutionFact não é modificado.

## Catálogo e interface

O Project Explorer oferece a associação somente quando um ExecutionFact está
selecionado. A escolha é feita diretamente entre os 55 itens do
`OFFICIAL_NORMATIVE_CATALOG`. Criterion, Requirement e Execution Rule são
copiados da mesma definição, evitando combinações inventadas pela interface.

Associar, alterar ou remover um Binding não executa Validation, Compatibility,
Resolver, Kernel ou agregação.

## Persistência

A tabela `platform_execution_bindings` armazena identidade, vínculo com o
ExecutionFact, três identificadores normativos, origem, criação e metadados.
Uma restrição de unicidade garante um Binding por ExecutionFact, e a chave
estrangeira remove o Binding quando seu fato deixa de existir.

O store é específico e direto, sem ORM, Repository genérico ou cache.

## Limites

Esta camada não cria regras normativas nem verifica satisfação de critérios.
Ela apenas registra uma decisão manual de enquadramento que uma Sprint futura
poderá entregar ao `ExecutionContractResolver`.
