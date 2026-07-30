# CriterionExecutionContract

## 1. Objetivo

`CriterionExecutionContract` é o primeiro contrato que reúne, sem executar:

- um ExecutionFact;
- sua ExecutionValidation;
- sua ExecutionCompatibility;
- sua regra declarativa;
- a entrada correspondente do manifesto.

```text
ExecutionFact + ExecutionValidation + ExecutionCompatibility + ExecutionRule
                                  ↓
                      CriterionExecutionContract
```

O contrato é autocontido para consumo futuro. Ele não calcula pontuação, não
interpreta texto e não altera seus objetos de origem.

## 2. Conteúdo

O contrato contém:

- IDs do contrato, fato, validação, compatibilidade, regra, critério e
  requisito;
- estado de validação, computabilidade legal e computabilidade de execução;
- valor normativo unitário resolvido;
- regra de contagem e regra temporal;
- Measurement e Occurrences;
- fatos e documentos canônicos;
- documentos aceitos e fatos requeridos;
- regras de agregação, sobreposição e variante;
- tabela aplicável;
- referências de artigo e anexo;
- itens não resolvidos;
- rastreabilidades normativa, factual e de validação;
- explicação;
- ExecutionFact, ExecutionValidation e ExecutionCompatibility de origem.

## 3. Regras tipadas

`ResolvedCountingRule` transporta tipo, texto e fonte declarados.

`ResolvedVariantRule` transporta tipo, variantes possíveis e fato seletor. Ela
não escolhe uma variante.

`ResolvedNormativeValue` transporta o valor unitário oficial como Decimal, a
unidade, tabela, critério, fundamento jurídico e rastreabilidade até
`decree_criteria.json`. A conversão de vírgula decimal para Decimal é
normalização de representação, não cálculo.

As regras temporal, de agregação e de sobreposição são preservadas literalmente
como valores declarativos.

## 4. Preservação

Measurement, Occurrences, CanonicalFacts e CanonicalDocuments são os mesmos
objetos imutáveis existentes no ExecutionFact. A Validation completa também é
preservada como `source_validation`.
O resultado de compatibilidade é preservado como `source_compatibility`.

Essa composição evita reconstrução, perda de informação ou divergência.

## 5. Invariantes

- um contrato por ExecutionFact;
- um contrato por ExecutionValidation;
- um contrato por ExecutionCompatibility;
- cobertura exata entre as três coleções;
- regra e manifesto correspondentes;
- objetos-fonte imutáveis;
- IDs determinísticos;
- nenhuma seleção, soma, dedução ou decisão.

## 6. Limitações

O contrato pode permanecer `BLOCKED`, `HUMAN_REVIEW_REQUIRED` ou
`TEXT_DEPENDENT`. A resolução representa união contratual, não autorização
jurídica ou satisfação do critério.

`legal_computability` preserva a classificação normativa. A
`execution_computability` informa se o contrato possui valor e medição
disponíveis após a Validation e se o tipo da Measurement é compatível com a
regra. Assim, um contrato pode ser juridicamente
`TEXT_DEPENDENT` e operacionalmente `EXECUTABLE`.
