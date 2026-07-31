# ADR-036 — Workspace Insights

**Status:** ACCEPTED
**Data:** 2026-07-31
**Decisores:** Equipe de Arquitetura

**Relacionada a:**

- `PRODUCT_VISION`;
- P-001 — Progressive Evaluation;
- P-003 — Everything Visible Is a Resource;
- P-004 — Projection Neutrality;
- ADR-034 — Presentation Workspace Navigation;
- ADR-035 — Resource Presentation Model;
- RFC-003 — Workspace Insights.

## Contexto

O ProcDocOrganizer possui uma camada de apresentação baseada em Presentation
Workspace, Navigation Intents, Workspace Snapshots, Resources, Projection
Services e Resource Inspector.

Resources representam elementos navegáveis. O usuário também precisa
compreender condições relevantes derivadas do Workspace, como fatos aguardando
Binding, Evidence sem Document, Documents não utilizados, projeto ainda não
avaliado, cobertura parcial, condições positivas e pendências.

Essas condições não são entidades nem Resources. São diagnósticos transitórios
e explicáveis da camada de apresentação.

## Decisão

Adotar Insight como projeção imutável, derivada e não persistente da camada de
apresentação. Insight descreve uma condição observável do Workspace, sua
relevância visual, seus Resources relacionados e ações declarativas.

Insight não representa entidade, Aggregate, regra normativa, Validation,
Compatibility, decisão jurídica ou fonte factual.

## Distinção conceitual

- Resource responde: “O que é este elemento?”
- Insight responde: “O que merece atenção neste contexto?”
- Navigation Intent responde: “O que o usuário deseja fazer?”

Os três conceitos são complementares e não assumem responsabilidades uns dos
outros.

## Estrutura oficial

Um Insight deverá conter:

- identity;
- category;
- severity;
- title;
- message;
- explanation;
- related_resources;
- available_actions;
- source_revision.

Opcionalmente, quando derivado de avaliação:

- evaluation_id;
- evaluation_revision.

## Insight Identity

A identidade será estável enquanto a mesma condição existir, determinística,
derivada e não persistida. Sua formação conceitual será:

```text
provider_id
+ insight_code
+ ResourceIdentity relevantes
+ discriminator opcional
```

Exemplos:

```text
binding.missing + ExecutionFact/fact-1
document.unused + Document/doc-4
project.not_evaluated + Project/project-1
```

A identidade não dependerá de mensagem traduzida, severidade, título, ordem,
horário de geração ou posição na coleção. Quando a condição deixar de existir,
o Insight não será produzido na projeção seguinte.

## Categorias

Categorias iniciais:

- `COVERAGE`;
- `VALIDATION`;
- `ORGANIZATION`;
- `COMPLETENESS`;
- `INFORMATION`.

A categoria organiza a natureza da observação e não determina automaticamente
sua severidade. Novas categorias exigem evolução explícita do contrato.

## Severidade

Severidades iniciais:

- `INFO`;
- `WARNING`;
- `ERROR`;
- `SUCCESS`.

A severidade possui finalidade exclusivamente visual e operacional. `ERROR`
significa alta prioridade de atenção, não necessariamente erro fatal,
impedimento jurídico, reprovação normativa ou bloqueio da avaliação. A
severidade nunca altera domínio ou Pipeline.

## Explicabilidade

Todo Insight possuirá mensagem objetiva e explicação compreensível de sua
origem, preservando o princípio:

> Nenhuma conclusão sai do sistema sem explicação.

A explicação não inventará interpretação normativa. Quando a origem for
Validation, Compatibility ou Evaluation, o Provider apenas traduzirá o
resultado existente.

## Resources relacionados

Resources serão representados por referências imutáveis:

```text
InsightResourceReference
├── identity: ResourceIdentity
└── role: InsightResourceRole
```

Papéis iniciais:

- `SUBJECT`;
- `SOURCE`;
- `RELATED`;
- `TARGET`.

Haverá no máximo um `SUBJECT`; duplicidades de identidade e papel serão
inválidas. Nunca serão armazenados Resource completo ou entidade de domínio.

## Available Actions

Insights poderão declarar, mas nunca executar, ações disponíveis. Tipos
iniciais sugeridos:

- `OPEN_RESOURCE`;
- `INSPECT_RESOURCE`;
- `REVEAL_RESOURCE`;
- `EXECUTE_EVALUATION`.

Ações de navegação produzirão Navigation Intents. Ações operacionais produzirão
intenções operacionais tipadas. `EXECUTE_EVALUATION` não será Navigation Intent.
A View não descobrirá ações consultando serviços ou domínio; o Provider
determinará sua disponibilidade na projeção.

## Insight Providers

Insights serão produzidos por Providers especializados, como futuros
BindingInsightProvider, DocumentInsightProvider, EvidenceInsightProvider,
EvaluationInsightProvider e CoverageInsightProvider.

Cada Provider possuirá `provider_id` estável, conjunto explícito de
`insight_code`, escopo documentado, identidade determinística e dependências
fornecidas por composição.

Providers não conhecem Views ou toolkit, não modificam Workspace, não persistem
Insights, não executam regras normativas, não substituem Validation ou
Compatibility e não usam Service Locator.

Contrato conceitual:

```text
provide(workspace_snapshot) → tuple[Insight, ...]
```

Dependências factuais adicionais serão tipadas e fornecidas no construtor. Não
serão usados `source_snapshot` genérico ou contêiner arbitrário de dados.

## Workspace Insight Service

Poderá existir um coordenador para executar Providers registrados, consolidar
resultados, rejeitar identidades duplicadas, preservar origem, ordenar
deterministicamente e produzir InsightCollection.

O serviço não poderá fundir mensagens por heurística, reinterpretar severidade,
eliminar Insights por semelhança textual, executar regras dos Providers,
alterar Workspace ou recalcular fatos e cobertura. Providers serão resolvidos
na composition root.

## InsightCollection

Será uma coleção imutável contendo insights, total, workspace_revision e
generated_at opcional. `generated_at` serve à apresentação e auditoria técnica,
não representa validade.

Ordenação determinística recomendada:

1. prioridade visual;
2. categoria;
3. insight_code;
4. identidade.

## Validade e revisão

Insights não possuirão expiração temporal genérica. Cada Insight registrará a
revisão do Workspace de origem. Quando o Workspace mudar, serão projetados
novamente. Insights derivados de avaliação poderão registrar evaluation_id e
evaluation_revision.

A revisão, não o tempo, identificará projeções potencialmente obsoletas.

## Integração com Workspace

Workspace Snapshot e Navigation History não armazenarão Insights.

```text
Workspace Snapshot
        ↓
Insight Providers
        ↓
Workspace Insight Service
        ↓
InsightCollection
        ↓
Dashboard / Coverage / Review / outros consumidores
```

Ao restaurar um Workspace Snapshot, os Insights serão produzidos novamente.

## Relação com o Dashboard

O Workspace Dashboard poderá evoluir incrementalmente para consumir
InsightCollection. Será consumidor, não autoridade, e não poderá executar
Providers, criar severidades, deduplicar diagnósticos, recalcular cobertura,
modificar ou persistir Insights.

## Relação com Coverage Analyzer

O Coverage Analyzer não calculará cobertura a partir de Insights:

```text
estado operacional existente
        ↓
Coverage Analyzer
        ↓
Coverage Result
        ↓
Coverage Insight Provider
        ↓
Insights
```

Coverage Result será a fonte estruturada de métricas. Insights serão projeções
orientadas à atenção e navegação, preservando P-004.

## Não persistência

Insights nunca serão persistidos como autoridade nem exigirão registro de
criação ou exclusão. Serão derivados novamente do Workspace Snapshot, dos
resultados operacionais existentes e das fontes tipadas dos Providers.
Persistência futura de histórico analítico exigirá ADR própria.

## Limite crítico

Insight não poderá se transformar em segunda Validation, segunda Compatibility,
motor de pontuação, sistema de elegibilidade, fonte normativa ou mecanismo de
correção automática.

Um Provider poderá projetar condições como “ExecutionFact aguardando Binding”,
“Evidence sem Document” e “Projeto ainda não avaliado”. Não poderá decidir que
um critério deveria ser atendido, que um Binding está juridicamente correto,
que uma pontuação deveria mudar ou que uma incompatibilidade pode ser ignorada.

## Compatibilidade

O modelo será independente de Qt, Web, CLI, toolkit e persistência. Views
receberão apenas DTOs de apresentação.

## Consequências

Benefícios:

- diagnósticos uniformes;
- Dashboard orientado à ação;
- reutilização entre funcionalidades;
- navegação consistente;
- explicabilidade e baixo acoplamento;
- suporte futuro a Coverage Analyzer e Review Workspace;
- compatibilidade com futura interface Web.

Custos:

- Providers especializados;
- disciplina na definição de códigos;
- controle explícito de identidade e origem;
- nova projeção quando o Workspace mudar.

## Não objetivos

Esta ADR não implementa Workspace Insight Service, Insight Providers, Coverage
Analyzer, migração do Dashboard, persistência de Insights, notificações, IA ou
OCR. Esses elementos serão tratados em Sprints posteriores.

## Princípio derivado

### P-005 — Insight Derivation

Insights são projeções derivadas e explicáveis do estado atual do Workspace.
Nunca constituem fonte factual, normativa ou decisória.

## Decisão final

O ProcDocOrganizer adotará Insight como DTO imutável, derivado e não persistente
da camada de apresentação.

Todo Insight possuirá identidade determinística, categoria, severidade visual,
mensagem, explicação, referências a ResourceIdentity, ações declarativas e
revisão de origem.

Insight Providers traduzirão condições operacionais ou resultados já
produzidos. Nunca substituirão Validation, Compatibility, Kernel ou regras
normativas.
