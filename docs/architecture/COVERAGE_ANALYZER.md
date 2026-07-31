# Coverage Analyzer

## Significado de Overall Coverage

`covered/total` contabiliza verificações estruturais: relação de Document, presença de Document em Evidence, presença de ExecutionFact em Evidence e Binding factual. Não é quantidade homogênea de objetos, pontuação, suficiência normativa, percentual geral de prontidão ou nível de aprovação. Evidence contribui em dimensões estruturais distintas.

Quando existe Evaluation, referências de `CriterionScore` e `RequirementScore` são projetadas literalmente. Sem Evaluation, o estado normativo permanece `NOT_EVALUATED`.

O contrato atual de Coverage preserva identidade e estado. A pontuação continua pertencendo ao resultado de Evaluation e não é duplicada em `NormativeCoverageReference`.

**Release:** Beta 1.1
**Base:** ADR-037 — Coverage Analysis

## Objetivo e fluxo

Coverage é uma análise operacional, multidimensional, imutável e somente
leitura. Não atribui pontuação nem interpreta significado normativo.

```text
CoverageInput → CoverageAnalyzer → CoverageResult
```

Não há integração visual ou produção de Insights nesta Sprint.

## CoverageInput

Entrada normalizada composta por project ID/revision e referências imutáveis de
Documents, Evidences, ExecutionFacts, Bindings e Evaluation opcional. Ela não
contém entidades e não depende de Qt, SQLite, Views ou Stores.

O snapshot opcional de Evaluation contém apenas identidades utilizadas,
presença de resultados de Validation/Compatibility e estados normativos já
produzidos.

## CoverageAnalyzer

O Analyzer é determinístico e não possui dependências externas. Ele observa as
relações recebidas, produz contagens e findings, e nunca executa Pipeline,
Validation, Compatibility ou cálculo normativo.

## Escopos

- **Document:** total, utilizados, não utilizados, múltiplas Evidences e sem
  relacionamento;
- **Evidence:** presença independente de Documents e ExecutionFacts,
  participação na Evaluation e inconsistências estruturais;
- **Factual:** Binding, participação na Evaluation e presença de resultados de
  Validation e Compatibility;
- **Normative:** `NOT_EVALUATED` sem snapshot; com snapshot, contagem literal
  dos estados existentes de Requirement e Criterion;
- **Overall:** contagem de verificações estruturais cobertas e totais, com
  razão exata. Não calcula média nem percentual autoritativo.

## CoverageFinding

Cada Finding contém escopo, `ResourceIdentity` principal, estado, valores
observado/esperado, explicação, reason codes e identidades relacionadas. Não
armazena Resources completos ou entidades.

## CoverageResult

Agrega os cinco escopos, findings deterministicamente ordenados, revisões das
fontes, versão da análise e data opcional. `generated_at` permanece vazio no
Analyzer para que entradas iguais produzam resultados iguais.

## Estados

Os estados estruturais são `EMPTY`, `PARTIAL`, `COMPLETE`, `NOT_EVALUATED`,
`INCONSISTENT`, `UNKNOWN`, `ABSENT`, `INSUFFICIENT` e `NOT_APPLICABLE`.
Nenhum possui significado jurídico.

## Explicabilidade e fronteiras

Todo Finding possui explicação e reason code derivados diretamente das
relações observadas. Coverage referencia somente `ResourceIdentity`, não
consulta Insights e não modifica Workspace, Resources, Evaluation ou domínio.

## Fonte produtiva

No Productive Workspace, `CoverageInput` é construído a partir da sessão `.pdop`
ativa. `DocumentRepository.list_all()` fornece o catálogo completo; Evidences,
ExecutionFacts, Bindings e suas relações são lidos separadamente dos Stores da
mesma sessão. Nenhum Document é filtrado por ausência de Evidence.

`project_revision` recebe a revisão operacional persistida do Project. Ela não
é a revisão visual do `WorkspaceSnapshot`, a revisão da Evaluation nem
`platform_sdk.Project.revision`. O `CoverageAnalyzer` e seus contratos permanecem
inalterados.
