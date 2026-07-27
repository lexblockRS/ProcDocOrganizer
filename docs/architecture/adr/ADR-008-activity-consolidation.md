# ADR-008 — Consolidação de Activity

## Status

Aceito.

## Contexto

O domínio já possuía `Activity` como registro mínimo da atividade lembrada,
enquanto o pipeline de reconstrução introduziu
`FunctionalAssignmentEvidence` e `FunctionalExercise`. Sem uma definição
explícita, os três conceitos poderiam ser interpretados como representações
concorrentes do mesmo fato.

Esta decisão não cria outro tipo de atividade e não introduz interpretação
normativa.

## Decisão

`Activity` é a entidade que acompanha uma atividade profissional desde a
lembrança inicial até sua comprovação. Ela preserva a descrição fornecida pelo
usuário, registra o grau de consolidação da investigação e mantém referências
tipadas aos elementos factuais que a sustentam.

`FunctionalAssignmentEvidence` continua sendo uma afirmação documental
estruturada sobre um possível exercício. Seu estado pertence ao pipeline de
tratamento da própria evidência e não expressa o estado da `Activity`.

`FunctionalExercise` continua sendo o fato funcional reconstruído: exercício
contínuo de uma função, por uma pessoa, em um contexto e período. Seu estado é
temporal (ativo ou encerrado) e não expressa o grau de comprovação da
`Activity`.

## Estados de Activity

O fluxo inicial é pequeno e linear:

```text
lembrada
  → em investigação
  → parcialmente comprovada
  → comprovada
```

- **lembrada:** hipótese inicial ainda sem investigação;
- **em investigação:** busca e interpretação documental em andamento;
- **parcialmente comprovada:** existe sustentação documental, mas o fato ainda
  não foi completamente consolidado;
- **comprovada:** as evidências sustentam ao menos um exercício funcional
  reconstruído.

Classificação e enquadramento RSC permanecem fora desse fluxo. Uma sprint
futura poderá estender o ciclo após `comprovada`, no módulo consumidor
apropriado, sem alterar o significado factual dos estados atuais.

## Relações e cardinalidades

```text
Activity (1)
  ├── (0..*) FunctionalAssignmentEvidence
  └── (0..*) FunctionalExercise

FunctionalExercise (1)
  └── (0..*) FunctionalAssignmentEvidence
```

Uma `Activity` pode existir sem relações enquanto é apenas lembrada. Durante a
investigação, pode referenciar várias evidências de atribuição e vários
exercícios, inclusive para representar períodos descontínuos. Uma evidência
pode contribuir para mais de uma atividade conceitual; a referência não
transfere sua propriedade nem seu ciclo de vida. Cada exercício conserva sua
própria proveniência nas evidências usadas em sua reconstrução.

As relações são representadas por identificadores imutáveis. `Activity` não
cria, altera nem remove evidências ou exercícios. Evidências e exercícios têm
ciclo de vida independente e podem existir antes de serem associados a uma
atividade lembrada.

## Invariantes

- identidade e descrição da atividade são obrigatórias;
- estado e identificadores relacionados são tipados;
- uma relação não pode aparecer duplicada;
- comprovação parcial exige ao menos uma evidência relacionada;
- comprovação exige ao menos uma evidência e um exercício relacionados;
- transições não podem saltar etapas.

## Consequências

A lembrança do usuário e o fato reconstruído passam a possuir uma ligação
explícita sem se tornarem a mesma coisa. O modelo permanece neutro em relação
ao RSC: não contém pontuação, item normativo, enquadramento ou regra de
classificação.

Nesta etapa, as novas relações e evoluções de estado existem apenas no modelo
de domínio. O `InMemoryActivityRepository` é preservado e não é criada
persistência SQLite, CRUD, tela ou serviço adicional.
