# Changelog

Todas as mudanças relevantes do ProcDocOrganizer serão registradas neste
arquivo.

## [1.1.0-beta.1] — 2026-07-31

### Adicionado

- Productive Workspace integrado à MainWindow.
- Workspace Dashboard e Review Workspace.
- Resource Inspector, Workspace Insights e Coverage Analyzer.
- Results Explorer e Evaluation Report integrados.
- Navegação por Intents com histórico de voltar e avançar.
- Revisão operacional persistida por Project.
- Suporte estrutural a Documents sem Evidence.

### Alterado

- MainWindow consolidada como shell produtivo único.
- Project Explorer consolidado como perspectiva operacional.
- Dashboard e Review passaram a consumir composição neutra compartilhada.
- Serviços produtivos passaram a ser compostos por ProjectSession.
- Banco oficial dos serviços produtivos passou a ser o `database.db` do
  `.pdop`.
- DocumentRepository passou a ser a fonte oficial do catálogo documental.
- CoverageInput passou a receber Documents independentemente das relações com
  Evidence.

### Corrigido

- Navegação paralela entre Views e filtros fora do Workspace Context.
- Duplicação entre Findings e Insights.
- Evaluation tratada indevidamente como NavigationIntent.
- Projeção incompleta de Requirement Coverage.
- Histórico sem restauração funcional.
- ExecutionFact aparecendo como seleção vazia no Inspector.
- Autoridades concorrentes de Project e vazamento entre Projects.
- Rollback alterando Workspace antes da confirmação da troca.
- Documents sem Evidence invisíveis no Coverage produtivo.

### Arquitetura

- ApplicationLifecycleHost como autoridade única da sessão ativa.
- ProjectSession existente reutilizada como contexto operacional.
- Ativação transacional e rollback de troca de Project.
- Separação entre revisões operacional, do Workspace e da Evaluation.
- Insights e Coverage permanecem derivados e não persistidos.
- `productive-shell.sqlite` preservado somente como legado.

### Limitações conhecidas

- ExecutionFact não possui projector próprio e aparece como `UNAVAILABLE` no
  Inspector.
- Evaluation, Results e Report precisam ser regenerados após reabertura.
- Não existe importador automático para `productive-shell.sqlite`.
