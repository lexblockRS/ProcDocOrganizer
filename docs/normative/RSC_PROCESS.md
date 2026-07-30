# Processo RSC completo

## Objetivo

`RSCProcess` representa o ciclo completo de um processo de
Reconhecimento de Saberes e Competências. Ele reúne a identidade do
processo, servidor, instituição, nível pretendido, data e os snapshots
factuais e normativos produzidos durante a execução.

O Aggregate é uma fronteira de orquestração da aplicação. Ele não
pertence ao núcleo aritmético e não incorpora regras do Decreto nº
13.048/2026.

## Responsabilidades

O processo:

- preserva a identidade e os dados administrativos;
- agrega evidências documentais simples;
- preserva `ExecutionFact`, `ExecutionValidation`,
  `ExecutionCompatibility`, `CriterionScore` e `RequirementScore`;
- controla a progressão explícita entre estágios;
- rejeita critérios ausentes do `NormativeCriterionCatalog`;
- expõe pontuações, pendências, evidências usadas e alertas temporais;
- mantém cada revisão como um novo snapshot imutável.

O processo não valida fatos, decide compatibilidade, calcula pontuação,
agrega requisitos nem analisa alertas. Esses resultados são produzidos
pelos componentes especializados e apenas registrados no Aggregate.

## Modelo

```text
RSCProcess
├── process_id
├── server: RSCServer
├── institution: RSCInstitution
├── intended_level
├── process_date
├── evidences: RSCProcessEvidence[]
├── execution_facts: ExecutionFactCollection
├── validations: ExecutionValidationCollection
├── compatibilities: ExecutionCompatibilityCollection
├── criterion_scores: CriterionScoreCollection
├── requirement_scores: RequirementScoreCollection
└── result: RSCProcessResult?
```

`RSCProcessEvidence` preserva somente identidade documental, descrição,
metadados e referências opcionais a critérios oficiais. Não realiza
OCR, parsing, classificação ou interpretação.

`RSCProcessResult` é o snapshot consolidado entregue ao processo. Ele
contém total, critérios computáveis e não computáveis, pendências,
alertas temporais e evidências efetivamente utilizadas. O total é
produzido externamente; o Aggregate nunca o recalcula.

## Ciclo de vida

```text
DRAFT
  ↓ adicionar evidências (opcional)
EVIDENCE
  ↓ registrar fatos
FACTS
  ↓ registrar validações
VALIDATED
  ↓ registrar compatibilidades
COMPATIBLE
  ↓ registrar pontuações por critério
SCORED
  ↓ registrar agregações por requisito
AGGREGATED
  ↓ registrar resultado consolidado
CONSOLIDATED
```

As transições são explícitas e retornam uma nova instância. Uma etapa
não pode ser saltada. Coleções vazias são válidas e permitem representar
um processo sem fatos ou pontuação sem inventar conteúdo.

`aggregate_id` expõe a identidade estável do processo e corresponde ao
`process_id`, preservado em todas as revisões. `same_process(other)`
compara essa identidade de domínio. A igualdade padrão do `dataclass`
permanece estrutural: snapshots de revisões diferentes não são iguais,
mesmo quando pertencem ao mesmo processo. A retenção e a reconstrução
cronológica desses snapshots pertencem à camada de persistência.

## Fluxo completo

```text
Evidências documentais
        ↓
ExecutionFactBuilder
        ↓
ExecutionValidation
        ↓
ExecutionCompatibility
        ↓
CriterionExecutionContract
        ↓
CriterionScoringKernel
        ↓
CriterionScoreCollection
        ↓
RequirementScoreAggregator
        ↓
RequirementScoreCollection
        ↓
consolidação externa
        ↓
RSCProcessResult
```

O `RSCProcess` registra os resultados nas fronteiras indicadas, mas não
invoca nenhum desses componentes.

## Relação com o catálogo

O `NormativeCriterionCatalog` é a única fonte de identidade normativa.
Toda referência de critério em evidências, fatos, pontuações ou resultado
deve existir no catálogo oficial. O processo não cria definições,
políticas de compatibilidade, valores ou regras aritméticas.

## Invariantes

- identidade do processo, servidor e instituição são obrigatórias;
- `aggregate_id` permanece estável entre todas as revisões;
- igualdade estrutural e identidade de domínio são conceitos distintos;
- nível pretendido e data do processo são obrigatórios;
- evidências não podem repetir identidade;
- referências de critério devem existir no catálogo;
- validações e compatibilidades devem corresponder exatamente aos fatos;
- pontuações devem corresponder aos fatos e preservar critérios oficiais;
- agregações devem preservar todos os `CriterionScore`;
- o resultado só pode referenciar critérios, evidências e alertas
  pertencentes ao processo;
- snapshots, coleções e resultados são imutáveis;
- nenhuma transição executa cálculo normativo.

## Consultas

Após a consolidação, o processo consegue informar:

- pontuação por critério;
- pontuação por requisito;
- pontuação total consolidada;
- critérios não computáveis;
- pendências;
- alertas temporais;
- evidências associadas a um critério e evidências usadas no resultado.

## Limitações da V1

- não há persistência específica, repository ou banco para o processo;
- não há interface gráfica definitiva;
- não há importação automática, OCR, IA ou parser;
- evidências são referências documentais simples;
- a consolidação final continua sendo responsabilidade externa;
- o processo não introduz elegibilidade, ranking ou decisão jurídica.

Esta versão estabelece a representação e a continuidade do fluxo. A
execução operacional completa depende da composição, em uma camada de
serviço futura, dos componentes já existentes.
