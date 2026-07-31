# Workspace Dashboard

**Release:** Beta 1.1
**Autoridade atual:** Dashboard 2.0

O Dashboard é a leitura inicial e passiva do projeto. Ele não consulta Stores, não executa Coverage e não produz Insights.

```text
Application composition root
  ├─ CoverageAnalyzer -> CoverageResult
  └─ WorkspaceInsightService -> InsightCollection
             ↓
WorkspaceDashboardService
             ↓
WorkspaceDashboardViewModel -> DTOs imutáveis -> View
```

O mesmo `CoverageResult` e a mesma `InsightCollection` alimentam o Review Workspace. O Dashboard apresenta resumo e ações prioritárias; o Review é a fila operacional completa.

Toda navegação emitida pela View passa por `NavigationController.navigate()`. `EXECUTE_EVALUATION` produz `ExecuteEvaluationAction`, executada pelo Application Service existente, e nunca uma Navigation Intent disfarçada.

Os documentos anteriores à P-006, baseados em métricas locais, requirements projetados localmente e indicador próprio de saúde, são históricos e não normativos.

Consulte [DASHBOARD_2.md](DASHBOARD_2.md) e [REVIEW_WORKSPACE.md](REVIEW_WORKSPACE.md).

Na composition root produtiva iniciada por `app.py`, o Dashboard é registrado
como `workspace_dashboard` e torna-se a primeira perspectiva após abrir um
Project. A View continua passiva; navegação segue por Intent e avaliação segue
separadamente por `ExecuteEvaluationAction`.
