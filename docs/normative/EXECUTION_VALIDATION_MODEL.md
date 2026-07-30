# Modelo de Validação da Execução

## 1. Objetivo

`ExecutionValidation` descreve a aptidão estrutural de um `ExecutionFact` para
uma futura aplicação normativa. Ele não calcula pontos, não completa fatos e não
decide mérito.

Há correspondência exata:

```text
1 ExecutionFact → 1 ExecutionValidation
```

`ExecutionValidationCollection` preserva a ordem da coleção de entrada e rejeita
validações duplicadas para o mesmo fato.

## 2. Conteúdo

Cada validação contém:

- identidade própria e do ExecutionFact;
- critério e regra executável;
- estado;
- fatos, documentos, variantes e medições ausentes;
- fatos inconsistentes;
- estado de sobreposição;
- computabilidade declarada;
- bloqueios e alertas;
- rastreabilidade;
- explicação.

## 3. Lacunas tipadas

### MissingFact

Registra o nome exato exigido em `required_facts`, a regra e o motivo. O
Validator não procura sinônimos nem cria valores.

### MissingDocument

Registra ausência do documento da origem factual ou ausência integral de
documentos canônicos.

### MissingVariant

Registra regra de variante, opções possíveis e pendências. Uma variante não
selecionada continua ausente mesmo quando o fato de papel está disponível.

### MissingMeasurement

Registra tipo e unidade quando não existe quantidade com estado `AVAILABLE`.

### InconsistentFact

Registra campo, valor esperado, valor observado e motivo. Nenhuma inconsistência
é corrigida.

## 4. Rastreabilidade

`ExecutionValidationTraceability` relaciona:

- Validation;
- ExecutionFact;
- regra e manifesto;
- critério e requisito;
- documento normativo;
- documento factual;
- Assessment de origem.

O Validator também verifica as identidades internas das ocorrências e da
rastreabilidade normativa.

## 5. Imutabilidade

Todos os modelos usam dataclasses `frozen` e `slots`; todas as coleções são
tuplas. IDs são UUIDs v5 determinísticos derivados do `execution_fact_id`.

## 6. Limites

A Validation informa aptidão contratual. Ela não afirma que o critério foi
satisfeito e não representa elegibilidade, pontuação ou decisão administrativa.
