# ProcDocOrganizer Beta 1.1

**Versão técnica:** `1.1.0-beta.1`
**Tag preparada:** `v1.1.0-beta.1`
**Data:** 2026-07-31

## Objetivo

Consolidar o Workspace produtivo sobre o Core estabilizado na Beta 1.0,
oferecendo acompanhamento, revisão, navegação e avaliação explicáveis sem
transferir ao sistema a decisão normativa humana.

## Escopo entregue

- MainWindow como shell produtivo único;
- Dashboard, Review, Project Explorer, Results e Report como perspectivas;
- Resource Inspector, Insights e Coverage;
- histórico linear com restauração de filtros, seleção e Inspector;
- autoridade única da sessão e serviços project-scoped;
- revisão operacional persistida;
- catálogo canônico que inclui Documents sem Evidence.

## Fluxo produtivo

```text
app.py
  → Application
  → MainWindow
  → ProjectController
  → ProjectSessionFactory
  → ApplicationLifecycleHost.current_session
  → serviços project-scoped
  → Productive Workspace
```

O banco oficial é `<project>.pdop/database.db`.

## Decisões arquiteturais

A release materializa as ADRs 034 a 038: Workspace Navigation, Resources,
Insights, Coverage e Unified Project Authority. `ProjectManager` permanece
stateless; `WorkspaceSnapshot` representa somente estado visual; Coverage e
Insights são projeções derivadas e não persistidas.

## Validação de fechamento

- 1671 testes e 1434 subtestes aprovados;
- 69 testes arquiteturais e 215 subtestes arquiteturais aprovados;
- 506 arquivos Python analisados por AST;
- zero erros de AST;
- zero dependências proibidas;
- `compileall` e `git diff --check` aprovados.

## Compatibilidade e atualização

Projects `.pdop` existentes continuam usando o schema atual. A release não
cria migration nem altera `project.json`. Basta abrir o Project normalmente;
o pequeno estado operacional usa o chave–valor `index_state` já existente.

## Dados legados

`productive-shell.sqlite` é detectado e preservado, mas não é aberto como
autoridade, migrado, copiado ou associado automaticamente a um `.pdop`.

## Limitações conhecidas

- ExecutionFact aparece como `UNAVAILABLE` no Resource Inspector.
- Evaluation, Results e Report devem ser regenerados após reabertura.
- Não existe importador automático do banco produtivo legado.

Nenhuma tag foi criada e nenhum push foi realizado durante a preparação.
