# Criterion Score Model

## Contratos imutáveis

`CriterionScore`, `CriterionScoreCollection` e
`ScoringExecutionTrace` são dataclasses imutáveis e slotted.

Cada Score preserva:

- identidade estável derivada do `contract_id`;
- identidades de contrato, critério, requisito e regra;
- estado da execução;
- quantidade original e sua forma `Decimal`;
- operando normativo `Decimal`;
- operação aritmética e resultado;
- rastreabilidade até fato, validação e valor normativo;
- explicação legível;
- referência somente leitura ao contrato de origem.

`CriterionScoreCollection` rejeita identidades de Score duplicadas e
mais de um Score para o mesmo contrato.

## Estados

- `EXECUTED`: multiplicação autorizada e concluída.
- `BLOCKED`: `execution_computability` não era `EXECUTABLE`.
- `NOT_EXECUTED`: regra ou operando fora do recorte executável.
- `TEXT_DEPENDENT`: reservado pelo contrato público para uma etapa que
  precise representar dependência textual diretamente.
- `HUMAN_REVIEW_REQUIRED`: reservado pelo contrato público para revisão
  humana explícita.

Os dois últimos estados não promovem a computabilidade jurídica a uma
decisão do Kernel; contratos não executáveis continuam bloqueados.
