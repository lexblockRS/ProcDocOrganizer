# Execution Compatibility

## Objetivo

`ExecutionCompatibility` representa a verificação imutável entre o tipo
factual de uma `Measurement` e a regra normativa declarada para o critério.
Ela ocupa uma etapa própria:

```text
ExecutionFact
    ↓
ExecutionValidation
    ↓
ExecutionCompatibility
    ↓
CriterionExecutionContract
    ↓
CriterionScoringKernel
```

`ExecutionValidation` continua respondendo somente se o fato está completo e
consistente. O Kernel continua recebendo apenas contratos cuja
computabilidade já foi determinada.

## Políticas

As políticas atualmente reconhecidas são:

| Regra | Tipos admitidos |
|---|---|
| `PER_YEAR` | `DURATION` |
| `PER_MONTH` | `DURATION` |
| `PER_EVENT` | `COUNT`, `QUANTITY`, `HOURS` |
| `PER_PUBLICATION` | `COUNT`, `QUANTITY` |
| `CUSTOM_TEXT` | `COUNT`, `QUANTITY`, `HOURS` |

Além de pertencer ao conjunto admitido, o tipo observado deve corresponder ao
`measurement_type` declarado pela regra executável. Regra sem política
explícita é incompatível por segurança.

## Contrato

Cada `ExecutionCompatibility` conserva:

- identidades do fato, da validação e da regra;
- critério e requisito;
- regra de contagem;
- tipo observado, tipo declarado e tipos admitidos;
- estado `COMPATIBLE` ou `INCOMPATIBLE`;
- problemas e explicação;
- fato e validação imutáveis de origem.

A coleção exige correspondência exata e impede mais de um resultado por fato
ou por validação. Os identificadores são determinísticos.

## Limites

A etapa não:

- revalida completude factual;
- calcula quantidades ou pontos;
- modifica `ExecutionFact`, `ExecutionValidation` ou a regra;
- interpreta datas, texto legal ou suficiência documental;
- autoriza juridicamente a pontuação.

Uma incompatibilidade bloqueia a computabilidade de execução do contrato, mas
não altera o estado factual produzido pela Validation.
