# First End-to-End Workflow

## Objetivo

Este fluxo valida, por código e sem interface gráfica, que a plataforma e a
aplicação RSC conseguem representar uma utilização completa com os componentes
já existentes.

Nenhuma abstração nova é necessária.

## Fluxo executado

```text
platform_sdk.Project.create()
        ↓ application_id = "rsc"
RSCProcess.create()
        ↓
RSCProcessEvidence manual
        ↓
ExecutionFact manual
        ↓
ExecutionValidator
        ↓
ExecutionCompatibilityEvaluator
        ↓
ExecutionContractResolver
        ↓
CriterionScoringKernel
        ↓
CriterionScore
        ↓
RequirementScoreAggregator
        ↓
RequirementScore
        ↓
RSCProcessResult
        ↓
RSCProcess CONSOLIDATED
```

## Cenário de referência

O teste utiliza o critério `DEC13048-ANX-II-ITEM-07`, participação em
atividade de avaliação ou atuação como jurado, cuja regra executável é
`PER_EVENT`.

São informados manualmente:

- Project pertencente à Application `rsc`;
- Evidence ligada a um documento;
- Activity e FunctionalExercise canônicos;
- `ExecutionFact` com Measurement `COUNT`;
- três eventos;
- rastreabilidade factual até Evidence e Document.

O catálogo e os artefatos normativos resolvem o valor oficial de três pontos
por evento. O Kernel executa:

```text
3 eventos × 3 pontos/evento = 9 pontos
```

O agregador preserva o Score e produz nove pontos para o requisito
`DEC13048-ART3-II`. O resultado consolidado registra o critério computável,
Evidence utilizada, ausência de pendências e total de nove pontos.

## Responsabilidades preservadas

- Project mantém identidade e associação à Application;
- RSCProcess preserva snapshots e não calcula;
- ExecutionFact contém somente o fato informado;
- Validation verifica consistência factual;
- Compatibility usa a política do catálogo;
- Resolver produz contrato autocontido;
- Kernel executa apenas Decimal;
- Aggregator soma somente Scores executados;
- consolidação é montada externamente e entregue ao RSCProcess.

## Rastreabilidade

O resultado permite percorrer:

```text
CriterionScore
 → CriterionExecutionContract
 → ExecutionCompatibility
 → ExecutionValidation
 → ExecutionFact
 → Evidence
 → Document
```

Também preserva regra, critério, requisito, tabela, quantidade, operando,
fórmula e resultado.

## Snapshots e identidade

Renomear o Project cria nova revisão com o mesmo `aggregate_id`.
As transições do RSCProcess criam snapshots com o mesmo `process_id`.
Snapshots anteriores permanecem imutáveis e observáveis.

## Resultado

A arquitetura funciona ponta a ponta para o cenário determinístico suportado:

- plataforma genérica;
- Application RSC registrada;
- fato manual;
- validação;
- compatibilidade;
- resolução normativa;
- pontuação;
- agregação;
- consolidação rastreável.

Persistência, UI, OCR, SQLite e IA não participam deste fluxo.
