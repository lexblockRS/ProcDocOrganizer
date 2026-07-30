# ExecutionValidator

## 1. Arquitetura

```text
ExecutionFactCollection
        +
criterion_execution_rules.json
        +
execution_rules_manifest.json
        ↓
ExecutionValidator
        ↓
ExecutionValidationCollection
```

O Validator não acessa banco, repositories, Aggregate Roots ou Engines do
pipeline.

## 2. Inicialização

Os dois documentos podem ser fornecidos como mapeamentos somente leitura ou
carregados por `from_files()`. Antes da validação são conferidos:

- IDs únicos;
- mesma cobertura de critérios;
- correspondência entre regra e manifesto;
- requisito e tabela.

## 3. Verificações

### Fatos

Cada item de `required_facts` deve possuir um `CanonicalFactType` correspondente.
Aliases não declarados são rejeitados.

### Documentos

Deve existir ao menos um documento canônico. O documento da rastreabilidade
factual deve estar presente, com a mesma identidade, e permanecer relacionado às
ocorrências.

### Unidades

A unidade de Measurement, Occurrences e fatos quantitativos deve coincidir
literalmente com `measurement_unit` da regra.

### Tempo

Datas presentes devem usar ISO e o fim não pode anteceder o início. Regra
temporal diferente de `NONE` exige início. O Validator não calcula duração.

### Variantes

Opções devem coincidir com a regra. Disponibilidade do fato seletor é registrada,
mas a variante continua pendente enquanto não houver decisão em camada futura.

### Sobreposição

O estado deve ser coerente com `overlap_candidates`. `POSSIBLE`, `CONFIRMED` e
`UNKNOWN` exigem atenção humana; nenhuma resolução é executada.

### Medição

Measurement somente está completa quando possui quantidade e estado
`AVAILABLE`. O Validator não calcula a quantidade.

### Rastreabilidade

São comparadas identidades do fato, regra, critério, requisito, Assessment,
origem factual, documentos e ocorrências.

## 4. Precedência dos estados

1. qualquer bloqueio estrutural → `BLOCKED`;
2. variante, sobreposição ou revisão explícita → `HUMAN_REVIEW_REQUIRED`;
3. computabilidade textual → `TEXT_DEPENDENT`;
4. alerta não bloqueante → `READY_WITH_WARNINGS`;
5. ausência de pendências → `READY`.

## 5. Determinismo

A validação percorre os fatos na ordem recebida, não altera a coleção e produz o
mesmo ID e o mesmo resultado para entradas iguais.

## 6. Ausência de inferência

O Validator:

- não busca fatos em outros objetos;
- não converte unidades;
- não corrige datas;
- não escolhe variantes;
- não confirma sobreposição;
- não soma ocorrências;
- não interpreta texto jurídico;
- não calcula pontos.
