# Dashboard 2.0

O Dashboard existente agora consome exclusivamente `WorkspaceSnapshot`, `CoverageResult` e `InsightCollection`.

## Fluxo

```text
Estado operacional -> CoverageInput -> CoverageAnalyzer -> CoverageResult
CoverageResult -> Coverage Insight Providers -> WorkspaceInsightService
WorkspaceSnapshot + CoverageResult + InsightCollection
    -> WorkspaceDashboardViewModel -> DTOs -> WorkspaceDashboardView
```

`WorkspaceDashboardService` recebe os contratos oficiais já compostos. Não executa Coverage, não registra Providers, não cria Insights e não executa avaliação. A composição compartilhada pertence à composition root da aplicação.

`EXECUTE_EVALUATION` é representado por `ExecuteEvaluationAction`. Navegação e operação são sinais independentes da View.

O resumo vem do Workspace, as metricas vem de Coverage e todas as orientacoes vem de Insights. Acoes declarativas tornam-se Navigation Intents no ViewModel. Projetos sem dados mostram `0/0`; colecoes vazias possuem mensagem explicita; Insights sem acao continuam visiveis.

Nao existe percentual autoritativo. Como Coverage fornece dimensoes independentes para Evidence, a interface mostra “com/sem Documents” e “com/sem ExecutionFacts”, sem inventar uma intersecao denominada “completa”.

A View recebe apenas DTOs imutaveis; nao acessa dominio, Stores, SQLite, CoverageAnalyzer ou WorkspaceInsightService.

No shell produtivo, a mesma instância é atualizada depois da Evaluation e
depois da restauração de um Workspace Snapshot. Nenhum resultado de Coverage
ou Insight é guardado no histórico.
