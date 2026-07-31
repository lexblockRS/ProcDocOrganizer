# Execute Pipeline

## Fluxo completo

```text
Project
  ↓
Evidence
  ↓
ExecutionFact factual
  ↓
ExecutionBinding manual ou pendência operacional
  ↓
ExecutionValidation
  ↓
ExecutionCompatibility
  ↓
ExecutionContractResolver
  ↓
CriterionScoringKernel
  ↓
RequirementScoreAggregator
  ↓
RSCProcess consolidado
```

## Serviço de aplicação

`RSCExecutionService` é o único coordenador desse fluxo. Ele recebe um
Project, consulta stores específicos de Evidence, ExecutionFact e Binding,
separa fatos enquadrados daqueles ainda pendentes e
projeta os dados editoriais para os contratos imutáveis já exigidos pelo
pipeline.

Somente fatos com Binding percorrem Validation, Compatibility, Resolver e
Kernel. Fatos sem Binding são preservados como `RSCProcessPendingFact`, com a
mensagem **"ExecutionFact aguardando enquadramento."**. Nenhum Binding é
criado ou inferido.

O serviço não escolhe critérios. Criterion, Requirement e Execution Rule
chegam pelo Binding manual e são conferidos contra o
`OFFICIAL_NORMATIVE_CATALOG`. Medição, quantidade, unidade, período e origem
continuam vindo do ExecutionFact e da Evidence.

Após a projeção, o serviço apenas chama, em sequência:

1. `ExecutionValidator`;
2. `ExecutionCompatibilityEvaluator`;
3. `ExecutionContractResolver`;
4. `CriterionScoringKernel`;
5. `RequirementScoreAggregator`;
6. métodos de snapshot do `RSCProcess`.

Nenhum desses componentes foi modificado.

## Integração com a interface

O Project Explorer oferece **Executar Avaliação**. A UI solicita a execução
ao serviço e apresenta somente:

- fatos e Bindings processados;
- quantidades de CriterionScores e RequirementScores;
- pontuação total;
- incompatibilidades;
- tempo decorrido.

A tela não valida, resolve contratos ou calcula pontuação. Falhas tecnicamente
impeditivas interrompem a execução; a ausência de Binding é pendência
operacional e não impede Results ou Evaluation Report.

## Resultado e persistência

O resultado contém o `RSCProcess` consolidado e um resumo imutável da
execução. Nesta Sprint ele permanece somente em memória, pois não existe
infraestrutura de persistência adequada para esse Aggregate e nenhuma foi
criada.

## Rastreabilidade

O CriterionScore preserva o contrato, Validation, Compatibility, projeção
normativa do ExecutionFact, Evidence de origem e Binding que determinou os
identificadores normativos. IDs factuais não são substituídos.

Cada `RSCProcessEvidence` preserva todos os Documents da Evidence, inclusive
os ainda não utilizados por qualquer ExecutionFact.

## Limites

Não há seleção automática, regra nova, OCR ou IA. Dados administrativos ainda
não coletados pelo Project Explorer são representados no RSCProcess como não
informados. Uma evolução futura poderá coletá-los antes da execução sem
alterar o pipeline.
