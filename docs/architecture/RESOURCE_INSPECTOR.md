# Resource Inspector

**Release:** Beta 1.1
**Base:** ADR-034 e ADR-035

## Objetivo

O Resource Inspector é o primeiro consumidor visual do Resource Presentation
Model. Ele apresenta, de maneira uniforme, a identidade, o display, a metadata,
os relacionamentos e as ações declaradas por um Resource.

Nesta versão são projetados apenas Document, Evidence e Requirement.
ExecutionFact, Criterion, Evaluation e Report permanecem fora da integração.

## Fluxo

```text
Workspace Snapshot
       ↓
Selected ResourceIdentity
       ↓
ProjectionService
       ↓
Resource
       ↓
ResourceInspectorViewModel
       ↓
ResourceInspectorView
```

A composition root da interface observa o `PresentationContextStore`, traduz a
seleção do Workspace em `ResourceIdentity`, escolhe o projetor registrado e
entrega o Resource ao ViewModel. A View não participa dessa coordenação.

## ViewModel

`ResourceInspectorViewModel` depende apenas dos contratos de Resource e
Navigation Intent. Ele transforma Resource em DTOs frozen e slotted para:

- informações comuns;
- pares de metadata;
- relacionamentos navegáveis;
- ações declarativas;
- estados vazio, indisponível e pronto.

O ViewModel não conhece Qt, stores, persistência, domínio ou outros
ViewModels.

## View

`ResourceInspectorView` recebe exclusivamente `ResourceInspectorViewData`.
Ela renderiza os DTOs e emite `navigation_requested` com a Intent já projetada
pelo ViewModel.

A View não:

- consulta Resource ou entidades diretamente;
- resolve Projection Services;
- conhece outras Views;
- acessa Stores ou SQLite;
- executa navegação;
- executa ações declaradas.

## Relacionamentos e ações

Todo relacionamento mostra tipo, tipo do destino, identificador e rótulo. Um
clique solicita navegação por meio da Intent correspondente à identidade de
destino.

Somente ações presentes em `available_actions` são exibidas. A ação é
transportada como metadata escalar da Intent; o Inspector não contém callbacks
de negócio nem executa a operação.

## Estados

- **Nenhum Resource selecionado:** apresenta estado vazio consistente;
- **Projeção indisponível:** preserva tipo e ID quando conhecidos;
- **Sem metadata:** apresenta explicitamente a ausência;
- **Sem relacionamentos:** apresenta explicitamente a ausência;
- **Sem ações:** não cria ações implícitas e informa a ausência.

## Fronteiras

O Inspector é um adaptador Qt, mas seus DTOs e ViewModel são independentes de
toolkit. A integração permanece na composition root. Nenhuma regra normativa,
interpretação, cálculo ou alteração de domínio é realizada.

Na `MainWindow` produtiva, o Inspector permanece no dock lateral e reage ao
snapshot oficial tanto em navegações novas quanto em restaurações históricas.
Document, Evidence e Requirement são projetados; ExecutionFact selecionado sem
projector é exibido como `UNAVAILABLE`, nunca como estado vazio ou erro.
