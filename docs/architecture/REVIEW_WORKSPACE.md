# Review Workspace

O Review Workspace é o ambiente operacional de revisão do ProcDocOrganizer. Ele não é relatório, não substitui o Dashboard e não produz diagnósticos.

## Fluxo

```text
WorkspaceSnapshot + CoverageResult + InsightCollection
    -> ReviewWorkspaceService
    -> ReviewWorkspaceSnapshot
    -> ReviewWorkspaceViewModel
    -> ReviewWorkspaceView
    -> NavigationIntent
    -> Workspace Navigation
    -> Resource Inspector
```

O serviço usa Coverage para resumo e estado, mas a fila principal é formada exclusivamente por Insights. Findings permanecem na autoridade estrutural e são traduzidos por Providers somente quando merecem atenção visual. O serviço não chama `CoverageAnalyzer`, `WorkspaceInsightService`, domínio, SQLite ou toolkit.

## ReviewItem

Cada item imutável contém identidade própria, categoria, severidade, texto original, `ResourceIdentity` principal, identidades relacionadas, origem e uma intenção declarativa opcional. Entidades e Resources completos não são armazenados.

As únicas categorias são Documents, Evidences, ExecutionFacts, Requirements e Project. A ordenação determinística usa severidade (`ERROR`, `WARNING`, `INFO`, `SUCCESS`), categoria, título, identidade e, apenas como desempate total, `item_id`.

## Filtros e estados

Filtros usam `WorkspaceFilter` com os IDs `review.category`, `review.severity`, `review.origin` e `review.only_pending`. A solicitação passa pelo Navigation Service e o Review consome exclusivamente `WorkspaceSnapshot.active_filters`. Não existe estado autoritativo de filtro na View ou no Project Explorer.

## Navegação e Inspector

A View emite a `NavigationIntent` do item. O Navigation Service atualiza seleção e Workspace Snapshot; o Resource Inspector reage ao contexto publicado. Document, Evidence e Requirement possuem projetores. ExecutionFact preserva a Intent e abre a perspectiva operacional, mas continua indisponível no Inspector até existir projetor oficialmente autorizado.

`review_workspace` é uma perspectiva produtiva da `MainWindow`. Voltar restaura
seus filtros diretamente de `WorkspaceSnapshot.active_filters`; avançar retorna
ao Project Explorer e ao Resource selecionado sem repetir a Intent do item.
