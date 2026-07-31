# ProcDocOrganizer

**Release:** Beta 1.1
**Versão técnica:** `1.1.0-beta.1`

Plataforma desktop para organizar, rastrear e avaliar processos de
Reconhecimento de Saberes e Competências (RSC), preservando a decisão humana e
a explicação de cada resultado.

## Capacidades principais

- organização de Documents, Evidences, ExecutionFacts e Bindings;
- avaliação progressiva com pendências operacionais;
- Workspace Dashboard e Review Workspace;
- Resource Inspector;
- Coverage e Insights derivados;
- Results Explorer e Evaluation Report;
- navegação por Intents com voltar, avançar, filtros e restauração;
- isolamento e revisão operacional por Project.

## Execução

Requer Python e as dependências de `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python app.py
```

`app.py` inicia a única `MainWindow` produtiva. Ao abrir um Project, Dashboard,
Review, Project Explorer, Results e Evaluation Report são apresentados como
perspectivas do mesmo Workspace.

## Projects `.pdop`

Cada Project é um diretório `<nome>.pdop` contendo `project.json`,
`database.db`, Documents e diretórios operacionais. Os serviços produtivos usam
exclusivamente o `database.db` do Project ativo. `productive-shell.sqlite` é
apenas um artefato legado preservado e não é importado automaticamente.

## Limitações conhecidas

- ExecutionFact aparece como `UNAVAILABLE` no Inspector enquanto não houver
  projector próprio.
- Evaluation, Results e Report precisam ser regenerados após reabertura.
- Não existe importador automático para `productive-shell.sqlite`.

## Desenvolvimento

```powershell
python -m pytest -q
python -m compileall -q .
```

A arquitetura detalhada está em `docs/architecture/ARCHITECTURE_OVERVIEW.md`.
O histórico desta release está em `CHANGELOG.md` e
`docs/releases/BETA_1_1.md`.
