# Workspace Insights

> Integração atual: Providers são registrados pela composition root compartilhada. O Coverage Provider é neutro e não pertence ao Dashboard. A fila do Review consome Insights, não soma novamente os Findings que lhes deram origem.

`EXECUTE_EVALUATION` é ação operacional e produz `ExecuteEvaluationAction`; não é Navigation Intent.

**Release:** Beta 1.1
**Base:** ADR-036 — Workspace Insights

## Objetivo

Workspace Insights oferece contratos imutáveis para comunicar condições
relevantes do estado atual da apresentação. Insight é derivado, explicável e
não persistente. Não representa domínio, Validation, Compatibility, decisão
normativa ou fonte factual.

```text
WorkspaceSnapshot
       ↓
WorkspaceInsightProvider
       ↓
WorkspaceInsightService
       ↓
InsightCollection
       ↓
consumidores futuros
```

Esta fundação não integra Dashboard, Inspector ou qualquer nova View.

## InsightIdentity

`InsightIdentity` contém:

- `provider_id`;
- `insight_code`;
- `discriminator` opcional.

Os valores são normalizados e formam uma identidade determinística e não
persistida. Texto visual, severidade, posição e horário não participam da
identidade.

## Insight

`Insight` é frozen e slotted. Contém categoria, severidade visual, título,
mensagem, explicação, referências a Resources, ações declarativas e revisão do
Workspace de origem. `evaluation_id` e `evaluation_revision` são opcionais e
devem coexistir.

As categorias iniciais são Coverage, Validation, Organization, Completeness e
Information. As severidades Info, Warning, Error e Success possuem significado
exclusivamente visual. Nenhum desses valores altera o Pipeline.

## Resources e ações

`InsightResourceReference` aponta exclusivamente para `ResourceIdentity` e
declara um papel Subject, Source, Related ou Target. Um Insight aceita no
máximo um Subject e rejeita referências duplicadas.

`InsightAction` declara Open Resource, Inspect Resource, Reveal Resource ou
Execute Evaluation. As ações não possuem callbacks e não executam operações.

## InsightCollection

`InsightCollection` registra Insights, total, revisão do Workspace e data de
geração opcional. A coleção rejeita identidades duplicadas e aplica ordenação
determinística por prioridade visual, categoria, código e identidade.

## Providers

`WorkspaceInsightProvider` define:

```text
provide(workspace_snapshot) → tuple[Insight, ...]
```

Providers são compostos externamente e não conhecem Views, toolkit, domínio ou
persistência. Cada resultado deve preservar o `provider_id` e a revisão do
snapshot recebido.

O provider inicial `ProjectEvaluationInsightProvider` produz somente “Projeto
ainda não avaliado.” quando existe Project no Workspace e não existe avaliação
corrente. Ele consulta apenas campos do Workspace Snapshot.

## WorkspaceInsightService

O serviço recebe uma tupla explícita de Providers, rejeita IDs de Provider
duplicados, executa cada contrato, valida origem e revisão, rejeita identidades
de Insight duplicadas e produz `InsightCollection`.

Ele não altera mensagens ou severidades, não elimina resultados por semelhança,
não executa regras e não recalcula domínio.

## Serialização

`serialize_insight` e `serialize_insight_collection` convertem os DTOs em
estruturas de valores simples. A serialização não constitui persistência nem
autoridade histórica.

## Fronteiras

Workspace Snapshot e Navigation History não armazenam Insights. Mudanças de
revisão exigem nova projeção. Os módulos são independentes de Qt, Web, CLI,
SQLite, domínio, Kernel, Validation e Compatibility.
