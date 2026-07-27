# Baseline de Testes da Plataforma

## Identificação

- Data: 2026-07-27
- Branch: `feature/rsc-application`
- HEAD: `25d89af15a40bc7019133788656e60ad4b78a54a`
- Commit: `feat(rsc): implement functional exercise application layer`
- Escopo: estado completo do worktree, incluindo alterações locais anteriores
  ao PF-01
- Framework: `unittest`
- Ambiente gráfico: PySide6 em modo offscreen, configurado pelos testes Qt

O worktree já estava sujo no início do PF-01: 53 arquivos rastreados
modificados, 59 caminhos não rastreados e nenhum arquivo staged. O baseline
descreve esse estado integrado, não somente o conteúdo do HEAD.

## Comandos oficiais

Executar a partir da raiz do repositório, com o ambiente virtual existente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app.py applications contracts controllers core database models presentation services ui tests
git diff --check
```

Para executar isoladamente os testes de caracterização mais abrangentes:

```powershell
.\.venv\Scripts\python.exe -m unittest -v tests.test_rsc_pipeline_e2e tests.test_rsc_project_sqlite_lifecycle tests.test_document_engine_consolidation tests.test_application_contribution_lifecycle
```

## Dimensão do baseline

- 71 arquivos `test_*.py`;
- 836 métodos `test_*` declarados diretamente;
- 875 testes executados por descoberta, incluindo casos herdados dos
  contratos compartilhados de repository;
- 65 contextos `subTest` declarados.

O `unittest` inclui os casos concretos herdados em `testsRun`, mas não informa
uma contagem separada dos `subTest` bem-sucedidos. Por isso, o número oficial
de execução é 875 testes; 65 é a quantidade estática de contextos, não de
iterações dinâmicas.

## Mapa dos fluxos críticos

### A. Projeto

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Criar projeto | Adequada | `test_project_application_selection`, `test_project_manager_database` |
| Abrir e reabrir projeto | Adequada | `test_project_application_selection`, `test_rsc_project_sqlite_lifecycle` |
| Fechar projeto | Adequada | `test_project_session`, `test_application_contribution_lifecycle` |
| Resolver `application_id` | Adequada | `test_application_registry`, `test_project_application_selection` |
| Preservar metadados | Adequada | `test_project_application_selection` e testes de lifecycle SQLite |
| Criar, usar, fechar e recuperar dados | Adequada | `test_rsc_pipeline_e2e`, complementado por `test_rsc_project_sqlite_lifecycle` |

### B. Sessão

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Criar `ProjectSession` completa | Adequada | `test_project_session` |
| Criar `RscProjectSession` | Adequada | `test_rsc_project_session` |
| Disponibilizar serviços compartilhados | Adequada | `test_project_session` |
| Limpar referências no fechamento | Adequada | `test_project_session`, `test_evidence_lifecycle_characterization` |
| Isolar projetos consecutivos | Adequada | `test_rsc_pipeline_e2e`, `test_rsc_project_sqlite_lifecycle` |
| Liberar recursos externos | Parcial | Repositories não mantêm conexão SQLite aberta; não existe ainda um protocolo geral de descarte de sessão |

### C. Document Engine

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Importar e catalogar | Adequada | `test_document_acervo`, `test_document_engine_consolidation` |
| Detectar duplicidade | Adequada | os mesmos testes |
| Processar PDF e OCR | Adequada | `test_multi_parser_processing`, `test_ocr_pipeline`, `test_document_engine_consolidation` |
| Persistir resultado por página | Adequada | `test_document_indexer`, `test_document_engine_consolidation` |
| Indexar e pesquisar | Adequada | testes de search e index maintenance |
| Reabrir e recuperar catálogo/índice | Adequada | `test_document_engine_consolidation` |
| Preservar consistência em falha | Adequada | falhas de índice, rollback de remoção e rebuild transacional |

### D. Knowledge Engine

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Criar e atualizar Evidence | Adequada | `test_evidence_service`, `test_evidence_state_characterization` |
| Preservar proveniência | Adequada | `test_evidence_repository`, `test_search_to_evidence_flow` |
| Navegar Evidence → Document | Adequada | `test_module_integration_flows`, `test_project_controller_evidence_navigation` |
| Recuperar página e snippet | Adequada | `test_rsc_pipeline_e2e`, testes de documentos e busca |
| Persistir após reabertura | Adequada | `test_evidence_repository`, `test_rsc_project_sqlite_lifecycle` |
| Preservar evidência com fonte removida | Adequada | `test_document_engine_consolidation`, `test_activity_functional_flow` |

### E. Pipeline RSC

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Evidence → FunctionalAssignmentEvidence | Adequada | `test_rsc_pipeline_e2e`, testes de assignment |
| Assignment → FunctionalExercise | Adequada | `test_rsc_functional_exercise_from_assignment_evidences` |
| Exercise/Assignment → Activity | Adequada | `test_activity_functional_flow`, `test_rsc_pipeline_e2e` |
| Persistência integral | Adequada | `test_rsc_project_sqlite_lifecycle`, testes dos três repositories SQLite |
| Navegação reversa até documento, página e snippet | Adequada | `test_rsc_pipeline_e2e` |
| Ausência de estado residual entre projetos | Adequada | `test_rsc_pipeline_e2e`, `test_activities_sqlite_integration` |

### F. Presentation

| Fluxo | Estado | Proteção principal |
|---|---|---|
| Registrar e trocar views | Adequada | `test_view_manager` |
| Instalar, substituir e remover contribuições | Adequada | `test_desktop_contribution_installer`, `test_application_contribution_lifecycle` |
| Rollback de contribuição com falha | Adequada | os mesmos testes |
| Atualizar e limpar dashboard | Adequada | `test_dashboard_controller`, `test_dashboard_service`, `test_home_view_dashboard` |
| Preservar actions e menus | Adequada | `test_main_window_menu_host` |
| Navegação entre workspaces | Adequada | testes de documentos, busca, evidência e pipeline RSC |

## Cenários obrigatórios do PF-01

1. **Projeto completo:** protegido pelo pipeline end-to-end e pelos testes de
   reabertura real do `ProjectManager`.
2. **Sessões consecutivas:** protegido pelas trocas comum → RSC → comum e
   pelos testes de isolamento de bancos e serviços.
3. **Pipeline funcional:** protegido de documento até Activity, com
   persistência e navegação reversa até página e snippet.
4. **Contribuições:** protegido desde a instalação até a limpeza, incluindo
   substituição e rollback.
5. **Falha controlada:** protegido em composição de sessão, instalação de
   contribuição, SQLite, indexação, persistência de evidência e remoção
   documental.

Não foram adicionados testes no PF-01 porque os cenários obrigatórios já
possuíam caracterização explícita. Duplicá-los aumentaria o custo da suíte sem
preencher uma lacuna comportamental.

## Lacunas deliberadamente adiadas

- Não existe protocolo geral de descarte de sessão; o baseline protege o
  comportamento atual de limpeza de referências e de adapters sem conexão
  permanente.
- Não há aplicação fictícia de plataforma; ela pertence a uma fase posterior.
- O baseline não proíbe acoplamentos Host → RSC; essa restrição pertence ao
  PF-02 e às fases posteriores.
- Não há teste de plugins, discovery dinâmico, SDK ou segunda aplicação.
- Os testes atuais validam o worktree integrado e ainda não representam uma
  release imutável enquanto as alterações anteriores permanecerem sem commit.

## Resultado registrado

Na coleta inicial do PF-01:

```text
Ran 875 tests in 13.031s
OK
```

Esse total deve ser tratado como o mínimo reproduzível para o estado descrito
neste documento. Alterações futuras podem aumentar a quantidade, mas não
devem remover cobertura ou alterar os fluxos caracterizados sem uma decisão
explícita.
