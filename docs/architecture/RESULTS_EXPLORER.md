# Results Explorer

## Objetivo

O Results Explorer apresenta, sem recalcular, como o resultado de uma
avaliação RSC foi construído. A navegação parte do Requirement e alcança
Criterion, ExecutionFact, Evidence e Document.

## Arquitetura

```text
RSCProcess
    ↓
ResultsViewModel
    ↓
Presentation DTOs imutáveis
    ↓
ResultsView
```

`ResultsViewModel` é a única fronteira que conhece o snapshot de
`RSCProcess`. Ele não acessa banco, stores ou infraestrutura, não executa
Validation, Compatibility ou Kernel e não altera objetos recebidos.

`ResultsView` conhece somente DTOs específicos da apresentação. Ela não
importa nem consulta Aggregates, Scores, Bindings, fatos ou Evidences do
domínio.

## DTOs

As projections imutáveis são:

- `ResultsSummary`;
- `RequirementResultView`;
- `CriterionResultView`;
- `ExecutionFactResultView`;
- `EvidenceResultView`;
- `DocumentResultView`.

Elas transportam apenas texto, identificadores, estados, valores `Decimal` e
outras projections. Não possuem comportamento ou regras.

## Navegação

A árvore visual segue:

```text
Requirement
└── Criterion
    └── ExecutionFact
        └── Evidence
            └── Document
```

Selecionar um Criterion apresenta pontuação, fato, Evidence e Documents
relacionados. Evidence sem Document recebe indicação explícita, sem criação
de referência fictícia.

## Integração

Após **Executar Avaliação**, o Project Explorer mantém o resultado somente em
memória e habilita **Ver Resultado**. Esse comando cria o ViewModel, obtém o
`ResultsSummary` e abre a view passiva.

## Decisão arquitetural

O contrato solicitou registrar a decisão como ADR-008, mas esse número já
identifica historicamente “Consolidação de Activity”. A decisão foi registrada
como extensão do ADR-007 — Camada de Apresentação e Projeções, que já governa
essa fronteira:

> Componentes visuais nunca consomem Aggregates do domínio diretamente. Toda
> comunicação entre domínio e UI ocorre por ViewModels e DTOs específicos de
> apresentação.

Isso evita substituir ou duplicar decisões existentes.

## Limites

Não há gráficos, animações, persistência do RSCProcess, navegação inversa,
OCR, IA ou cálculo. A tela reflete exclusivamente o snapshot já consolidado.
