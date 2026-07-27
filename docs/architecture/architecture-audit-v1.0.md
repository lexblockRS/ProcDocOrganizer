# Architecture Audit v1.0

## 1. Identificação da auditoria

| Campo | Valor |
|---|---|
| Data e hora da coleta | 2026-07-25 19:39:45 (UTC-03:00) |
| Branch atual | `feature/rsc-application` |
| Commit atual | `25d89af15a40bc7019133788656e60ad4b78a54a` — `feat(rsc): implement functional exercise application layer` |
| Alterações não commitadas | Sim |
| Diretório raiz | `C:\Users\lexbl\OneDrive\Área de Trabalho\Unipampa\ProcDocOrganizer\ProcDocOrganizer` |
| Método | Inspeção estática de arquivos, símbolos e imports; aplicação e testes não executados |

O workspace continha cinco arquivos rastreados modificados e arquivos não
rastreados em `applications/rsc`, `docs/architecture` e `tests`. Esta auditoria
descreve o diretório de trabalho, não apenas o último commit.

## 2. Estrutura completa do projeto

Foram ignorados somente `.git`, `venv`, `__pycache__`, `.pytest_cache`,
`build`, `dist` e arquivos temporários.

### 2.1 Árvore

```text
ProcDocOrganizer/
├── app.py
├── ARCHTECTURE.md
├── LICENSE
├── README.md
├── requirements.txt
├── applications/
│   ├── __init__.py
│   └── rsc/
│       ├── __init__.py
│       ├── application.py
│       ├── assemblers/
│       │   ├── __init__.py
│       │   ├── functional_assignment_evidence_assembler.py
│       │   └── manual_functional_exercise_assembler.py
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── create_activity.py
│       │   ├── create_functional_assignment_evidence.py
│       │   ├── create_functional_exercise.py
│       │   └── create_project.py
│       ├── dto/
│       │   ├── __init__.py
│       │   ├── activity.py
│       │   ├── functional_exercise.py
│       │   └── project.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── activity.py
│       │   ├── functional_assignment_evidence.py
│       │   ├── functional_exercise.py
│       │   └── project.py
│       ├── ports/
│       │   ├── __init__.py
│       │   ├── activity_repository.py
│       │   ├── functional_exercise_repository.py
│       │   └── project_repository.py
│       ├── queries/__init__.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── in_memory_activity_repository.py
│       │   ├── in_memory_functional_exercise_repository.py
│       │   └── in_memory_project_repository.py
│       └── services/
│           ├── __init__.py
│           ├── create_activity_service.py
│           ├── create_functional_exercise_service.py
│           ├── create_project_service.py
│           ├── functional_assignment_normalizer.py
│           └── list_functional_exercises_service.py
├── contracts/
│   ├── __init__.py
│   ├── application.py
│   ├── application_contribution.py
│   └── navigation.py
├── controllers/
│   ├── __init__.py
│   ├── documents_controller.py
│   ├── evidence_controller.py
│   └── search_controller.py
├── core/
│   ├── __init__.py
│   ├── application.py
│   ├── application_registry.py
│   ├── CHANGELOG.md
│   ├── contribution_manager.py
│   ├── exceptions.py
│   ├── project_controller.py
│   ├── project_manager.py
│   ├── project_session.py
│   ├── project_session_factory.py
│   └── project_state.py
├── database/
│   ├── __init__.py
│   ├── database.py
│   ├── migrations.py
│   └── schema.py
├── docs/
│   ├── architecture/
│   │   ├── adr/
│   │   │   ├── README.md
│   │   │   ├── ADR-003-functional-assignment-normalizer.md
│   │   │   ├── ADR-004-functional-activity-taxonomy.md
│   │   │   ├── ADR-005-identity-profile-and-evidence-discovery.md
│   │   │   └── ADR-006-identity-resolution.md
│   │   ├── architecture-audit-v1.0.md
│   │   ├── domain-vision.md
│   │   └── functional-reconstruction-pipeline.md
│   ├── ARCHTECTURE_GUIDELINES.md
│   ├── CODEX_INSTRUCTIONS.md
│   ├── DATA_MODEL.md
│   ├── domain-model.md
│   ├── FUNCTIONAL_SPECIFICATION.md
│   ├── MULTI_PARSER_ARCHITECTURE.md
│   ├── navigation-model.md
│   ├── SEARCH_ARCHITECTURE_DECISIONS.md
│   ├── SPRINTS.md
│   └── workflow.md
├── models/
│   ├── __init__.py
│   ├── document.py
│   ├── document_read_models.py
│   ├── document_type.py
│   ├── evidence.py
│   ├── evidence_draft.py
│   ├── evidence_requests.py
│   ├── evidence_source_candidate.py
│   ├── project.py
│   └── search_result.py
├── services/
│   ├── __init__.py
│   ├── document_importer.py
│   ├── document_repository.py
│   ├── document_service.py
│   ├── document_source_resolver.py
│   ├── evidence_repository.py
│   ├── evidence_repository_errors.py
│   ├── evidence_repository_port.py
│   ├── evidence_service.py
│   ├── indexing/{__init__.py,document_indexer.py,indexing_result.py}
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── document_classifier.py
│   │   ├── document_metadata_extractor.py
│   │   ├── document_processor.py
│   │   ├── processing_repository.py
│   │   ├── processing_result.py
│   │   ├── text_extractor.py
│   │   ├── ocr/{__init__.py,ocr_engine.py,ocr_result.py,page_classifier.py,text_merger.py}
│   │   └── parsers/{__init__.py,default_registry.py,document_parser.py,parser_errors.py,parser_registry.py,pdf_parser.py}
│   ├── search/
│   │   ├── __init__.py
│   │   ├── contracts.py
│   │   ├── exceptions.py
│   │   ├── legacy_indexed_search_service.py
│   │   ├── maintenance_contracts.py
│   │   ├── search_filters.py
│   │   ├── search_index.py
│   │   ├── search_index_maintainer.py
│   │   ├── search_index_source.py
│   │   ├── search_query_builder.py
│   │   ├── search_result.py
│   │   ├── search_service.py
│   │   ├── sqlite_fts_index_maintainer.py
│   │   └── sqlite_fts_search_index.py
│   ├── search_document_source_resolver.py
│   ├── search_service.py
│   └── sqlite_evidence_repository.py
├── tests/
│   ├── test_application_contract.py
│   ├── test_application_contribution.py
│   ├── test_application_contribution_lifecycle.py
│   ├── test_application_registry.py
│   ├── test_contribution_manager.py
│   ├── test_database.py
│   ├── test_desktop_contribution_installer.py
│   ├── test_document_indexer.py
│   ├── test_document_metadata_extractor.py
│   ├── test_document_navigation.py
│   ├── test_document_service.py
│   ├── test_document_widgets.py
│   ├── test_documents_workspace_infrastructure.py
│   ├── test_evidence_architecture.py
│   ├── test_evidence_controller.py
│   ├── test_evidence_lifecycle_characterization.py
│   ├── test_evidence_repository.py
│   ├── test_evidence_service.py
│   ├── test_evidence_source_candidate.py
│   ├── test_evidence_state_characterization.py
│   ├── test_evidence_workspace.py
│   ├── test_evidence_workspace_state_matrix.py
│   ├── test_main_window_menu_host.py
│   ├── test_module_integration_flows.py
│   ├── test_multi_parser_processing.py
│   ├── test_ocr_pipeline.py
│   ├── test_project_application_selection.py
│   ├── test_project_controller_evidence_navigation.py
│   ├── test_project_manager_database.py
│   ├── test_project_session.py
│   ├── test_rsc_application.py
│   ├── test_rsc_application_layer.py
│   ├── test_rsc_functional_assignment_evidence_assembler.py
│   ├── test_rsc_functional_assignment_evidence_domain.py
│   ├── test_rsc_functional_assignment_normalizer.py
│   ├── test_rsc_functional_domain.py
│   ├── test_rsc_functional_exercise_application_layer.py
│   ├── test_rsc_list_functional_exercises_service.py
│   ├── test_rsc_manual_functional_exercise_assembler.py
│   ├── test_rsc_project_application_layer.py
│   ├── test_search_architecture.py
│   ├── test_search_index_maintenance.py
│   ├── test_search_service.py
│   ├── test_search_to_evidence_flow.py
│   └── test_search_workspace.py
└── ui/
    ├── __init__.py
    ├── constants/__init__.py
    ├── contribution_installer.py
    ├── dialogs/{__init__.py,base_dialog.py,new_project_dialog.py}
    ├── main_window.py
    ├── views/{__init__.py,base_view.py,documents_workspace.py,evidence_workspace.py,home_view.py,pdf_view.py,search_workspace.py}
    └── widgets/{__init__.py,document_list_widget.py,document_metadata_widget.py,document_page_list_widget.py,document_text_widget.py,evidence_editor_widget.py,evidence_list_widget.py,evidence_source_status_widget.py,project_tree_widget.py,search_panel.py,search_preview_widget.py,search_results_widget.py}
```

Um arquivo textual na raiz chamado `how 5e6719b -- \`` contém saída colorida
de um comando Git. Foi tratado como artefato temporário e não como módulo.

### 2.2 Arquivos Python: responsabilidade e linhas

As contagens incluem comentários e linhas em branco.

#### Host, contratos, controllers, banco e modelos

| Arquivo | Linhas | Responsabilidade aparente |
|---|---:|---|
| `app.py` | 16 | Ponto de entrada. |
| `contracts/__init__.py` | 11 | Fachada de contratos. |
| `contracts/application.py` | 26 | Protocolo de aplicação conectável. |
| `contracts/application_contribution.py` | 34 | Contribuição imutável de ação. |
| `contracts/navigation.py` | 31 | Pedido de navegação documental. |
| `controllers/__init__.py` | 10 | Exporta controllers. |
| `controllers/documents_controller.py` | 201 | Coordena catálogo e navegação documental. |
| `controllers/evidence_controller.py` | 381 | Coordena edição e persistência de evidências. |
| `controllers/search_controller.py` | 180 | Coordena pesquisa e seleção. |
| `core/__init__.py` | 0 | Marcador de pacote. |
| `core/application.py` | 78 | Composition root Qt. |
| `core/application_registry.py` | 104 | Registro e resolução de aplicações. |
| `core/contribution_manager.py` | 71 | Snapshot de contribuições. |
| `core/exceptions.py` | 5 | Erro compartilhado de contribuição. |
| `core/project_controller.py` | 843 | Orquestra o fluxo desktop. |
| `core/project_manager.py` | 123 | Cria e abre projetos. |
| `core/project_session.py` | 20 | Dependências de uma sessão. |
| `core/project_session_factory.py` | 52 | Compõe serviços por projeto. |
| `core/project_state.py` | 62 | Estado do projeto aberto. |
| `database/__init__.py` | 18 | Fachada de banco. |
| `database/database.py` | 79 | Conexão e transação SQLite. |
| `database/migrations.py` | 89 | Migrations versionadas. |
| `database/schema.py` | 81 | DDL do banco e FTS. |
| `models/__init__.py` | 30 | Fachada de modelos. |
| `models/document.py` | 131 | Documento importado serializável. |
| `models/document_read_models.py` | 55 | Projeções de leitura documental. |
| `models/document_type.py` | 20 | Tipos documentais. |
| `models/evidence.py` | 176 | Evidência imutável validada. |
| `models/evidence_draft.py` | 104 | Estado temporário do editor. |
| `models/evidence_requests.py` | 125 | Requests de criação/atualização. |
| `models/evidence_source_candidate.py` | 149 | Candidato de fonte de evidência. |
| `models/project.py` | 165 | Projeto físico e `project.json`. |
| `models/search_result.py` | 18 | Resultado legado de pesquisa. |

#### Aplicação RSC

| Arquivo | Linhas | Responsabilidade aparente |
|---|---:|---|
| `applications/__init__.py` | 5 | Exporta aplicações. |
| `applications/rsc/__init__.py` | 5 | Exporta RSC. |
| `applications/rsc/application.py` | 20 | Identidade e contribuições RSC. |
| `applications/rsc/assemblers/__init__.py` | 13 | Exporta assemblers. |
| `applications/rsc/assemblers/functional_assignment_evidence_assembler.py` | 45 | Monta atribuição funcional documental. |
| `applications/rsc/assemblers/manual_functional_exercise_assembler.py` | 53 | Monta exercício manual. |
| `applications/rsc/commands/__init__.py` | 15 | Exporta comandos. |
| `applications/rsc/commands/create_activity.py` | 10 | Comando de atividade. |
| `applications/rsc/commands/create_functional_assignment_evidence.py` | 20 | Comando de atribuição documental. |
| `applications/rsc/commands/create_functional_exercise.py` | 19 | Comando de exercício. |
| `applications/rsc/commands/create_project.py` | 10 | Comando de projeto RSC. |
| `applications/rsc/dto/__init__.py` | 7 | Exporta DTOs. |
| `applications/rsc/dto/activity.py` | 12 | DTO de atividade. |
| `applications/rsc/dto/functional_exercise.py` | 21 | DTO de exercício. |
| `applications/rsc/dto/project.py` | 12 | DTO de projeto RSC. |
| `applications/rsc/models/__init__.py` | 35 | Exporta domínio RSC. |
| `applications/rsc/models/activity.py` | 15 | Atividade mínima. |
| `applications/rsc/models/functional_assignment_evidence.py` | 190 | Evidência funcional e transições. |
| `applications/rsc/models/functional_exercise.py` | 277 | Value objects e agregado funcional. |
| `applications/rsc/models/project.py` | 15 | Projeto RSC mínimo. |
| `applications/rsc/ports/__init__.py` | 11 | Exporta portas. |
| `applications/rsc/ports/activity_repository.py` | 15 | Porta de atividades. |
| `applications/rsc/ports/functional_exercise_repository.py` | 21 | Porta de exercícios. |
| `applications/rsc/ports/project_repository.py` | 15 | Porta de projetos RSC. |
| `applications/rsc/queries/__init__.py` | 1 | Pacote de queries vazio. |
| `applications/rsc/repositories/__init__.py` | 13 | Exporta repositórios em memória. |
| `applications/rsc/repositories/in_memory_activity_repository.py` | 19 | Atividades em memória. |
| `applications/rsc/repositories/in_memory_functional_exercise_repository.py` | 28 | Exercícios em memória. |
| `applications/rsc/repositories/in_memory_project_repository.py` | 19 | Projetos RSC em memória. |
| `applications/rsc/services/__init__.py` | 21 | Exporta serviços. |
| `applications/rsc/services/create_activity_service.py` | 39 | Caso de uso de atividade. |
| `applications/rsc/services/create_functional_exercise_service.py` | 45 | Caso de uso de exercício. |
| `applications/rsc/services/create_project_service.py` | 39 | Caso de uso de projeto. |
| `applications/rsc/services/functional_assignment_normalizer.py` | 49 | Normalização funcional. |
| `applications/rsc/services/list_functional_exercises_service.py` | 32 | Consulta de exercícios. |

#### Serviços

| Arquivo | Linhas | Responsabilidade aparente |
|---|---:|---|
| `services/__init__.py` | 57 | Fachada de serviços. |
| `services/document_importer.py` | 176 | Copia documentos e calcula SHA/páginas. |
| `services/document_repository.py` | 180 | Catálogo JSON de documentos. |
| `services/document_service.py` | 172 | Read models documentais. |
| `services/document_source_resolver.py` | 9 | Porta de disponibilidade. |
| `services/evidence_repository.py` | 21 | Alias de compatibilidade. |
| `services/evidence_repository_errors.py` | 19 | Erros do repositório. |
| `services/evidence_repository_port.py` | 27 | Porta CRUD de evidência. |
| `services/evidence_service.py` | 234 | Casos de uso de evidência. |
| `services/indexing/__init__.py` | 9 | Exporta indexação. |
| `services/indexing/document_indexer.py` | 413 | Indexação e rebuild. |
| `services/indexing/indexing_result.py` | 48 | Resultados de indexação. |
| `services/processing/__init__.py` | 29 | Fachada de processamento. |
| `services/processing/document_classifier.py` | 18 | Classifica por nome. |
| `services/processing/document_metadata_extractor.py` | 329 | Extrai metadados. |
| `services/processing/document_processor.py` | 175 | Orquestra processamento. |
| `services/processing/processing_repository.py` | 104 | JSON de processamento. |
| `services/processing/processing_result.py` | 87 | Resultado processado. |
| `services/processing/text_extractor.py` | 40 | Texto nativo de PDF. |
| `services/processing/ocr/__init__.py` | 21 | Exporta OCR. |
| `services/processing/ocr/ocr_engine.py` | 95 | Contrato e Tesseract. |
| `services/processing/ocr/ocr_result.py` | 20 | Resultados de OCR. |
| `services/processing/ocr/page_classifier.py` | 39 | Decide necessidade de OCR. |
| `services/processing/ocr/text_merger.py` | 53 | Mescla texto e OCR. |
| `services/processing/parsers/__init__.py` | 17 | Exporta parsers. |
| `services/processing/parsers/default_registry.py` | 23 | Registry padrão. |
| `services/processing/parsers/document_parser.py` | 25 | ABC de parser. |
| `services/processing/parsers/parser_errors.py` | 21 | Erros de parser. |
| `services/processing/parsers/parser_registry.py` | 57 | Registro de parsers. |
| `services/processing/parsers/pdf_parser.py` | 86 | Parser PDF multiparte. |
| `services/search/__init__.py` | 75 | Fachada de pesquisa. |
| `services/search/contracts.py` | 192 | Contratos de consulta. |
| `services/search/exceptions.py` | 45 | Erros de pesquisa. |
| `services/search/legacy_indexed_search_service.py` | 50 | Adaptador legado. |
| `services/search/maintenance_contracts.py` | 186 | Contratos de manutenção. |
| `services/search/search_filters.py` | 74 | Filtros. |
| `services/search/search_index.py` | 11 | Porta de consulta. |
| `services/search/search_index_maintainer.py` | 24 | Porta de manutenção. |
| `services/search/search_index_source.py` | 13 | Porta da fonte. |
| `services/search/search_query_builder.py` | 123 | SQL/FTS parametrizado. |
| `services/search/search_result.py` | 16 | Resultado legado interno. |
| `services/search/search_service.py` | 89 | Serviço atual. |
| `services/search/sqlite_fts_index_maintainer.py` | 473 | Manutenção FTS SQLite. |
| `services/search/sqlite_fts_search_index.py` | 174 | Consulta FTS SQLite. |
| `services/search_document_source_resolver.py` | 37 | Disponibilidade via SQLite. |
| `services/search_service.py` | 53 | Fachada legada externa. |
| `services/sqlite_evidence_repository.py` | 183 | Persistência SQLite de evidências. |

#### UI

| Arquivo | Linhas | Responsabilidade aparente |
|---|---:|---|
| `ui/constants/__init__.py` | 3 | Pacote de constantes vazio. |
| `ui/contribution_installer.py` | 249 | Instala menus e ações. |
| `ui/dialogs/__init__.py` | 9 | Exporta dialogs. |
| `ui/dialogs/base_dialog.py` | 25 | Base de diálogo. |
| `ui/dialogs/new_project_dialog.py` | 183 | Formulário de novo projeto. |
| `ui/main_window.py` | 584 | Shell desktop. |
| `ui/views/__init__.py` | 19 | Exporta views. |
| `ui/views/base_view.py` | 42 | Ciclo comum de view. |
| `ui/views/documents_workspace.py` | 142 | Tela de documentos. |
| `ui/views/evidence_workspace.py` | 150 | Tela de evidências. |
| `ui/views/home_view.py` | 85 | Tela inicial. |
| `ui/views/pdf_view.py` | 309 | Visualizador PDF. |
| `ui/views/search_workspace.py` | 93 | Tela de busca. |
| `ui/widgets/__init__.py` | 29 | Exporta widgets. |
| `ui/widgets/document_list_widget.py` | 77 | Lista documental. |
| `ui/widgets/document_metadata_widget.py` | 61 | Metadados. |
| `ui/widgets/document_page_list_widget.py` | 62 | Lista de páginas. |
| `ui/widgets/document_text_widget.py` | 36 | Texto de página. |
| `ui/widgets/evidence_editor_widget.py` | 96 | Editor de evidência. |
| `ui/widgets/evidence_list_widget.py` | 86 | Lista de evidências. |
| `ui/widgets/evidence_source_status_widget.py` | 24 | Status da fonte. |
| `ui/widgets/project_tree_widget.py` | 110 | Árvore de projeto. |
| `ui/widgets/search_panel.py` | 61 | Entrada de busca. |
| `ui/widgets/search_preview_widget.py` | 39 | Preview de hit. |
| `ui/widgets/search_results_widget.py` | 56 | Lista de hits. |

#### Testes

Todos os 45 arquivos abaixo são artefatos de caracterização/verificação.

| Arquivo | Linhas | Responsabilidade aparente |
|---|---:|---|
| `tests/test_application_contract.py` | 72 | Contrato Application. |
| `tests/test_application_contribution.py` | 143 | Contribuições. |
| `tests/test_application_contribution_lifecycle.py` | 408 | Ciclo de contribuições. |
| `tests/test_application_registry.py` | 170 | Registry. |
| `tests/test_contribution_manager.py` | 172 | ContributionManager. |
| `tests/test_database.py` | 135 | Banco/migrations. |
| `tests/test_desktop_contribution_installer.py` | 376 | Installer desktop. |
| `tests/test_document_indexer.py` | 339 | Indexador. |
| `tests/test_document_metadata_extractor.py` | 239 | Metadados. |
| `tests/test_document_navigation.py` | 43 | Navegação. |
| `tests/test_document_service.py` | 170 | Serviço documental. |
| `tests/test_document_widgets.py` | 122 | Widgets documentais. |
| `tests/test_documents_workspace_infrastructure.py` | 239 | Workspace/controller documental. |
| `tests/test_evidence_architecture.py` | 173 | Arquitetura de evidência. |
| `tests/test_evidence_controller.py` | 349 | Controller de evidência. |
| `tests/test_evidence_lifecycle_characterization.py` | 281 | Ciclo de evidência. |
| `tests/test_evidence_repository.py` | 332 | Repositório de evidência. |
| `tests/test_evidence_service.py` | 317 | Serviço de evidência. |
| `tests/test_evidence_source_candidate.py` | 148 | Candidato de fonte. |
| `tests/test_evidence_state_characterization.py` | 541 | Estados de evidência. |
| `tests/test_evidence_workspace.py` | 122 | Workspace de evidência. |
| `tests/test_evidence_workspace_state_matrix.py` | 290 | Matriz visual. |
| `tests/test_main_window_menu_host.py` | 212 | Menus do host. |
| `tests/test_module_integration_flows.py` | 128 | Integração documental/evidência. |
| `tests/test_multi_parser_processing.py` | 180 | Multiparser. |
| `tests/test_ocr_pipeline.py` | 245 | OCR. |
| `tests/test_project_application_selection.py` | 161 | Seleção de aplicação. |
| `tests/test_project_controller_evidence_navigation.py` | 148 | Navegação do controller. |
| `tests/test_project_manager_database.py` | 26 | Banco na criação. |
| `tests/test_project_session.py` | 261 | Sessão. |
| `tests/test_rsc_application.py` | 138 | Aplicação RSC. |
| `tests/test_rsc_application_layer.py` | 132 | Atividade RSC. |
| `tests/test_rsc_functional_assignment_evidence_assembler.py` | 290 | Assembler funcional. |
| `tests/test_rsc_functional_assignment_evidence_domain.py` | 369 | Domínio da atribuição. |
| `tests/test_rsc_functional_assignment_normalizer.py` | 203 | Normalizador. |
| `tests/test_rsc_functional_domain.py` | 634 | Domínio funcional. |
| `tests/test_rsc_functional_exercise_application_layer.py` | 284 | Aplicação de exercício. |
| `tests/test_rsc_list_functional_exercises_service.py` | 184 | Listagem de exercícios. |
| `tests/test_rsc_manual_functional_exercise_assembler.py` | 232 | Assembler manual. |
| `tests/test_rsc_project_application_layer.py` | 135 | Projeto RSC. |
| `tests/test_search_architecture.py` | 401 | Arquitetura de busca. |
| `tests/test_search_index_maintenance.py` | 256 | Manutenção do índice. |
| `tests/test_search_service.py` | 224 | Serviço de busca. |
| `tests/test_search_to_evidence_flow.py` | 138 | Busca para evidência. |
| `tests/test_search_workspace.py` | 351 | UI de busca. |

## 3. Inventário completo das classes

### 3.1 Núcleo e contratos

| Classe (arquivo) | Responsabilidade | Atributos | Métodos públicos | Observação |
|---|---|---|---|---|
| `Application` (`core/application.py`) | Composition root | `app`, janela, state, manager, registry, factory, installer, controller | `run` | Cria objetos concretos. |
| `Application` Protocol (`contracts/application.py`) | Contrato de módulo | `application_id`, `display_name` | `can_open`, `contributions` | Protocolo. |
| `ActionContribution` (`contracts/application_contribution.py`) | Ação contribuída | id, label, menu, callback, ordem | dataclass | Imutável. |
| `DocumentNavigationRequest` (`contracts/navigation.py`) | Navegação até fonte | identidade, página | dataclass | Imutável. |
| `ApplicationRegistry` (`core/application_registry.py`) | Registro/resolução | `_applications` | `applications`, `register`, `get`, `resolve` | Trata ids legados. |
| `ApplicationRegistryError`, `DuplicateApplicationError`, `ApplicationNotRegisteredError`, `IncompatibleApplicationError` | Erros do registry | — | herdados | Exceções. |
| `ContributionManager` (`core/contribution_manager.py`) | Snapshot de contribuições | `_active` | `active`, `clear`, `activate`, `replace` | Não composto no bootstrap atual. |
| `ContributionError` (`core/exceptions.py`) | Erro compartilhado | — | herdados | Exceção. |
| `ProjectState` (`core/project_state.py`) | Projeto aberto | `_current_project` | `current_project`, `has_project`, `open_project`, `close_project` | Estado simples. |
| `ProjectSession` (`core/project_session.py`) | Lifetime de projeto | project, repositories/services, application | dataclass | Imutável. |
| `ProjectSessionFactory` (`core/project_session_factory.py`) | Composição por projeto | `_application_registry` | `create` | Instancia adapters. |
| `ProjectManager` (`core/project_manager.py`) | Criar/abrir `.pdop` | — | `create_project`, `open_project` | Também cria diretórios/banco. |
| `ProjectController` (`core/project_controller.py`) | Orquestra desktop | window, manager, state, session, processor, três controllers | `new_project`, `open_project`, `import_documents`, views, evidências, close, processamento | 843 linhas; várias responsabilidades observáveis. |

### 3.2 Modelos compartilhados

| Classe (arquivo) | Responsabilidade | Atributos | Métodos públicos |
|---|---|---|---|
| `Project` (`models/project.py`) | Projeto físico | nome, path, timestamps, application, version, database | `create`, `project_file`, serialização, `save`, `load` |
| `Document` (`models/document.py`) | Documento importado | nome, path, SHA, páginas, tipo/status/processamento | `create`, serialização |
| `DocumentType` | Enum de tipos | valores do enum | Enum |
| `DocumentAvailability` | Enum de disponibilidade | available/missing/unknown | Enum |
| `DocumentSummary` | Read model resumido | identidade, nome, tipo, datas/status | dataclass |
| `DocumentDetails` | Read model detalhado | summary, metadados, OCR/erro/páginas | dataclass |
| `DocumentPageSummary` | Read model de página | identidade, página, texto, fonte | dataclass |
| `Evidence` (`models/evidence.py`) | Evidência imutável | id, documento, página, textos, datas, timestamps | `create`, `now`, `with_changes` |
| `EvidenceDraft` | Estado de edição | id, documento, página e campos editáveis | `empty`, factories, requests, `is_minimally_valid` |
| `CreateEvidenceRequest`, `UpdateEvidenceRequest` | Entradas validadas | campos da evidência | inicialização validada |
| `EvidenceSourceCandidate` | Ponte busca/documento→evidência | identidade, página, snippet e metadados | `from_search_result`, `from_search_hit`, `suggest_title` |
| `SearchResult` (`models/search_result.py`) | Resultado legado | documento, página, snippet, termos | dataclass |

### 3.3 RSC

| Classe (arquivo) | Responsabilidade | Atributos | Métodos públicos |
|---|---|---|---|
| `RscApplication` | Integra RSC ao host | id, display name | `can_open`, `contributions` |
| `Activity` | Atividade mínima | id, descrição, estado | dataclass |
| `applications.rsc.models.Project` | Projeto RSC | id, título, status | dataclass |
| `FunctionalExerciseId` | UUID do exercício | `value` | `from_string` |
| `FunctionalExerciseType` | Tipo funcional | code, label | validação dataclass |
| `FunctionalRole` | Papel funcional | name | validação dataclass |
| `FunctionalContext` | Contexto institucional | organization, unit, reference | validação dataclass |
| `FunctionalExerciseStatus` | Estado temporal | ACTIVE, ENDED | Enum |
| `FunctionalPeriod` | Intervalo inclusivo | start/end | `is_open`, `is_closed`, `duration_days`, `contains`, `overlaps`, `ends_before` |
| `FunctionalExercise` | Agregado funcional | id, pessoa, tipo, papel, contexto, período, status | `is_active`, `is_ended`, `was_active_on`, `overlaps`, `end` |
| `FunctionalAssignmentEvidenceId` | UUID da interpretação | value | `from_string` |
| `SourceEvidenceReference` | Referência opaca | value | representação textual |
| `FunctionalAssignmentEvidenceStatus` | Estado do pipeline | RAW/NORMALIZED/IDENTIFIED/LINKED | Enum |
| `FunctionalAssignmentEvidence` | Afirmação funcional documental | id, pessoa, fonte, tipo, papel, organização, datas, status | `mark_normalized`, `mark_identified`, `mark_linked` |
| Quatro `Create*Command` | Entradas de casos de uso | dados específicos | dataclass |
| `ActivityDTO`, `ProjectDTO`, `FunctionalExerciseDTO` | Saídas dos casos de uso | campos projetados | dataclass |
| `ActivityRepository`, `ProjectRepository`, `FunctionalExerciseRepository` | Portas | — | CRUD/listagem específicos |
| Três `InMemory*Repository` | Adapters voláteis | coleção interna | operações das portas |
| `ManualFunctionalExerciseAssembler`, `FunctionalAssignmentEvidenceAssembler` | Montagem de domínio | — | `assemble` |
| `CreateActivityService`, `CreateProjectService`, `CreateFunctionalExerciseService`, `ListFunctionalExercisesService` | Casos de uso | repositório/assembler | `execute` |
| `FunctionalAssignmentNormalizer` | Normalização | — | `normalize` |

### 3.4 Serviços, persistência, processamento e busca

| Classes | Arquivo/grupo | Responsabilidade | Atributos e métodos principais |
|---|---|---|---|
| `ProjectDatabase` | `database/database.py` | Conexão/transação | path, connection; `open`, `initialize`, `transaction`, `close` |
| `DatabaseError`, `SchemaVersionError`, `FTS5UnavailableError`, `MigrationError` | `database/migrations.py` | Erros de banco | Exceções sem atributos próprios |
| `DocumentImporter` | `services/document_importer.py` | Importação física | project; `import_file(s)`, `remove_imported_files` |
| `DocumentRepository` | `services/document_repository.py` | Catálogo JSON | project/documents; `load`, `save`, CRUD |
| `DocumentService` e 3 erros | `services/document_service.py` | Leitura documental | repositories/resolver; list/get documento/página |
| `DocumentSourceResolver` | `services/document_source_resolver.py` | Porta | `is_document_available` |
| `EvidenceRepository` | `services/evidence_repository_port.py` | Porta CRUD | CRUD/list/count |
| `SQLiteEvidenceRepository` | `services/sqlite_evidence_repository.py` | Adapter SQLite | path/clock; CRUD/list/count |
| 4 erros de repository | `services/evidence_repository_errors.py` | Falhas de persistência | Exceções |
| `EvidenceService`, `EvidenceSourceStatus` e 5 erros | `services/evidence_service.py` | Casos de uso | repository/resolver/factories; CRUD, source, duplicates |
| `SearchDocumentSourceResolver` | `services/search_document_source_resolver.py` | Disponibilidade SQLite | path; `is_document_available` |
| `ProcessingResult`, `ProcessingRepository` | `services/processing` | Resultado e JSON | serialização, validação, load/list/save |
| `DocumentProcessor` | mesmo | Orquestra parser/metadados | extractor/registry; `process`, `get_valid_result` |
| `DocumentClassifier` | mesmo | Classificação nominal | `classify` |
| `DocumentMetadataExtractor` | mesmo | Regras de extração | `extract` |
| `TextExtractor` | mesmo | Texto PDF | `extract` |
| `DocumentParser`, `ParserRegistry`, `PDFParser` | `processing/parsers` | Abstração, registro e implementação | supports/parse/register/resolve |
| 5 `*ParserError` | `parser_errors.py` | Erros de parsing | Exceções |
| `OCREngine`, `TesseractOCREngine` | `processing/ocr` | Contrato/adapter OCR | config; `recognize_page` |
| `OCRResult`, `MergedTextResult` | mesmo | Resultados OCR | dataclasses |
| `PageClassificationStrategy`, `TextThresholdStrategy`, `PageClassifier` | mesmo | Política de OCR | limiares/strategy; suficiência/`requires_ocr` |
| `TextMerger` | mesmo | Merge | `merge` |
| `IndexingResult`, `RebuildError`, `RebuildReport` | `services/indexing` | Relatórios | dados/coleções; `successful`, add methods |
| `DocumentIndexer`, `IndexingValidationError` | mesmo | Manutenção do índice | path/maintainer; index/remove/rebuild |
| `SearchMatchMode`, `SearchSort`, `SearchOptions`, `SearchQuery`, `SearchHit`, `SearchResultPage` | `search/contracts.py` | Contratos públicos | enums/dataclasses |
| `SearchFilters` | `search/search_filters.py` | Filtros | dataclass validada |
| `SearchIndex`, `SearchIndexMaintainer`, `SearchIndexSource` | `services/search` | Portas | search/upsert/remove/rebuild/reconcile/inspect/source |
| `SearchIndexPage`, `SearchIndexDocument`, `IndexMaintenanceIssue`, `IndexRebuildReport`, `IndexReconcileReport`, `SearchIndexStatus` | `maintenance_contracts.py` | Contratos de manutenção | dataclasses |
| `SearchQueryBuilder` | `search_query_builder.py` | SQL/FTS | build methods |
| `SearchService` atual | `search/search_service.py` | Consulta | `_index`; search e modos legados |
| `SqliteFtsSearchIndex` | `sqlite_fts_search_index.py` | Adapter consulta | path/factory/builder; `search`, `search_legacy` |
| `SqliteFtsIndexMaintainer` | `sqlite_fts_index_maintainer.py` | Adapter manutenção | path/clock; upsert/remove/rebuild/reconcile/inspect/fingerprint |
| `LegacyIndexedSearchService`, `services.search_service.SearchService`, dois `SearchResult` | vários | Compatibilidade | APIs de busca antigas |
| 11 classes `Search*Error` | `search/exceptions.py` | Hierarquia de falhas | Exceções |

### 3.5 UI e controllers

| Classe | Responsabilidade | Atributos | Métodos públicos |
|---|---|---|---|
| `MainWindow` | Shell Qt | actions, menus, stack, views, tree, dock/status | menu dinâmico, show/set/clear projeto, progresso/documento |
| `DesktopContributionInstaller`, `_MenuHost`, `_InstalledAction`, `ContributionInstallationError` | Menus contribuídos | host/installed | `active`, `install`, `clear`, `replace` |
| `BaseDialog`, `NewProjectDialog` | Diálogos | campos/botões/apps | getters do projeto |
| `BaseView`, `HomeView`, `PdfView`, `SearchWorkspace`, `EvidenceWorkspace`, `DocumentsWorkspace` | Telas | widgets/estado | ciclos e setters/navegação específicos |
| 12 classes `*Widget` | Componentes visuais | controles Qt | setters, getters, clear e seleção |
| `SearchController` | Busca | workspace/service/callbacks | search/select/navigate/evidence |
| `DocumentsController` | Documentos | workspace/service/catalog/seleção | load/refresh/navigate/select/clear |
| `EvidenceEditorMode`, `EvidenceController` | Editor de evidência | workspace/service/drafts/mode/callbacks | load/select/create/update/save/cancel/delete/guard/navigate |

### 3.6 Classes auxiliares de testes

Todos os `*Tests`/`*Test` são `unittest.TestCase`, com fixtures em `setUp` ou
nos casos e métodos públicos `test_*`. Também foram encontradas estas classes
auxiliares: `ExampleApplication`, `ApplicationSpy`, `InstallerSpy`, `StateSpy`,
`ServiceControllerSpy`, `WindowSpy`, `FakeApplication`, `MenuHost`,
`FailingAddMenu`, `FailingRemoveMenu`, `TrackingAction`, `RecordingIndexer`,
`DocumentRepositoryDouble`, `ProcessingRepositoryDouble`, `LifecycleWorkspace`,
`CountingService`, `FailingListService`, `FailingSaveService`, `SignalDouble`,
`WorkspaceDouble`, `ServiceDouble`, `RecordingWorkspace`, `FailingService`,
`WorkspaceSnapshot`, `DocumentsWorkspaceDouble`, `EvidenceWorkspaceDouble`,
`FakeParser`, `FakeTextExtractor`, `FakeOCREngine`, `EvidenceControllerSpy`,
`ContributionInstallerSpy`, `FailingFactory`, `AssemblerSpy`, `RepositorySpy`,
`ReadOnlyRepositorySpy`, `FakeSearchIndex`, `Source` e `FailingMaintainer`.
Elas reproduzem apenas a API necessária do colaborador testado e mantêm
atributos de chamadas, resultados ou falhas programadas.

## 4. Inventário das funções globais relevantes

| Função | Arquivo | Responsabilidade |
|---|---|---|
| `main` | `app.py` | Instancia `Application` e inicia Qt. |
| `initialize_database` | `database/database.py` | Inicializa banco e migrations. |
| `get_schema_version`, `apply_migrations` | `database/migrations.py` | Consulta/aplica schema. |
| `_apply_migration_v1/v2/v3` | mesmo | DDL interno versionado. |
| `create_default_parser_registry` | `processing/parsers/default_registry.py` | Compõe parser PDF padrão. |
| `_normalize_request`, `_initialize_request` | `models/evidence_requests.py` | Validação interna de requests. |
| `_required_text`, `_optional_text` | `functional_assignment_evidence.py` | Validação textual interna. |
| `_normalized_text`, `_optional_normalized_text` | `functional_exercise.py` | Normalização textual interna. |
| `_non_negative` | `search/maintenance_contracts.py` | Valida contadores. |

## 5. Dependências entre módulos

### 5.1 Imports internos e grafo

```text
app.py
  → core.application.Application
      → PySide6.QApplication
      → ui.MainWindow
      → ProjectState
      → ProjectManager
      → ApplicationRegistry → applications.RscApplication
      → ProjectSessionFactory
      → DesktopContributionInstaller
      → ProjectController

ProjectController
  → MainWindow / NewProjectDialog / QMessageBox / QFileDialog
  → ProjectManager / ProjectState / ProjectSessionFactory
  → SearchController → SearchService → SearchIndex
  → DocumentsController → DocumentService
  → EvidenceController → EvidenceService → EvidenceRepository
  → DocumentImporter
  → DocumentProcessor → ParserRegistry → PDFParser

ProjectSessionFactory
  → ApplicationRegistry
  → DocumentRepository → documents.db.json
  → ProcessingRepository → processing/*.json
  → DocumentService
  → SearchService → SqliteFtsSearchIndex → SQLite FTS5
  → EvidenceService
      → SQLiteEvidenceRepository → ProjectDatabase → SQLite
      → SearchDocumentSourceResolver → ProjectDatabase

MainWindow
  → ui.views
      → ui.widgets
      → models / services.search contracts

applications.rsc.services
  → commands
  → assemblers
  → models
  → ports
  → dto

applications.rsc.repositories.in_memory
  → applications.rsc.models
```

### 5.2 Matriz resumida de imports

| Origem | Destinos internos | Tipo observado |
|---|---|---|
| `core.application` | `applications`, `core.*`, `ui.*` | Forte: cria concretos. |
| `core.project_controller` | `controllers`, `services`, `ui` | Forte: chama APIs concretas e Qt. |
| `core.project_manager` | `database`, `models.project` | Forte. |
| `core.project_session_factory` | `models`, `services`, `services.search` | Forte: composition factory. |
| `controllers` | `contracts`, `models`, serviços e workspaces | Forte para objetos; fraca para callbacks. |
| `ui` | `models`, `services.search`, widgets/views | Forte de apresentação. |
| `services` | `models`, `database`, search/processing | Forte nos adapters. |
| `services.search` | contratos/portas e SQLite | Fraca nos Protocols; forte nos adapters. |
| `services.processing` | models, parsers, OCR | Fraca nas ABCs; forte na composição concreta. |
| `applications.rsc.services` | commands, assemblers, models, ports, DTOs | Fraca quanto às portas; forte nos demais tipos. |
| `contracts.application` | `models.Project` | Dependência conceitual compartilhada. |

Dependência forte significa import concreto, instanciação direta ou acesso a
API específica. Dependência fraca significa `Protocol`, ABC, callback ou
colaborador recebido.

### 5.3 Dependências circulares

Nenhum ciclo direto de imports entre módulos de produção foi encontrado na
inspeção estática. Há colaboração bidirecional em runtime entre views e
controllers por sinais/callbacks, mas não ciclo de import. Fachadas
`__init__.py` reexportam muitos tipos e tornam a origem menos explícita sem
formar ciclo observado.

Existem APIs paralelas, não circulares:

- `services/search_service.py` adapta `services.search`;
- `services/evidence_repository.py` reexporta o adapter SQLite;
- `models.SearchResult`, `services.search.SearchResult` e `SearchHit` coexistem.

## 6. Fluxo de execução

### 6.1 Inicialização

```text
app.main()
  → Application()
      → QApplication(sys.argv)
      → configura nome/organização/versão
      → MainWindow()
          → ações
          → menus
          → toolbar
          → QStackedWidget + views
          → ProjectTreeWidget + splitter
          → QDockWidget Propriedades
          → status bar
      → ProjectState()
      → ProjectManager()
      → ApplicationRegistry([RscApplication()])
      → ProjectSessionFactory(registry)
      → DesktopContributionInstaller(MainWindow)
      → ProjectController(...)
          → DocumentProcessor
          → SearchController
          → DocumentsController
          → EvidenceController
          → callbacks, close guard e sinais
  → Application.run()
      → MainWindow.show()
      → QApplication.exec()
```

A `QApplication` antecede widgets. A aplicação inicia sem projeto, na
`HomeView`.

### 6.2 Criação de projeto

```text
action_new_project
  → ProjectController.new_project
  → EvidenceController.can_leave
  → NewProjectDialog(nome, pasta, aplicação)
  → ProjectManager.create_project
      → <pasta>/<nome>.pdop
      → cria documents/cache/exports/logs/temp
      → Project.create
      → initialize_database(database.db) → migrations 1..3
      → Project.save → project.json
      → remove pasta parcial em falha
  → ProjectController._load_project
```

### 6.3 Abertura de projeto

```text
action_open_project
  → guarda de alterações
  → QFileDialog.getExistingDirectory
  → ProjectManager.open_project
      → exige project.json
      → Project.load
      → atualiza last_opened_at
      → Project.save
  → ProjectSessionFactory.create
      → resolve Application
      → carrega DocumentRepository
      → compõe DocumentService, SearchService e EvidenceService
  → instala/substitui contributions
  → ativa session e ProjectState
  → injeta serviços nos controllers
  → MainWindow.set_project
  → DocumentsController.load
```

### 6.4 Fechamento

`close_project` consulta o editor, limpa contribuições, remove serviços dos
controllers, elimina sessão/seleção, fecha `ProjectState` e limpa a janela. O
evento de fechamento da própria janela usa o mesmo `can_leave` por callback.

### 6.5 Documentos e processamento

```text
Importar
  → DocumentImporter valida/copia
  → SHA-256 + páginas PDF
  → Document
  → DocumentRepository.add/save

Selecionar na árvore
  → ProjectController
  → propriedades + PdfView

Processar
  → DocumentProcessor
  → ParserRegistry.resolve
  → PDFParser
      → TextExtractor
      → PageClassifier
      → OCREngine quando necessário
      → TextMerger
  → DocumentMetadataExtractor
  → ProcessingRepository.save
  → DocumentIndexer / FTS
  → atualiza Document e UI
```

O lote seleciona resultados inválidos/ausentes, aplica limite, exibe
`QProgressDialog`, permite cancelamento e registra falhas individuais.

### 6.6 Pesquisa

`SearchWorkspace` emite eventos para `SearchController`, que usa
`services.search.SearchService` e `SqliteFtsSearchIndex`. A saída atual é
`SearchResultPage` contendo `SearchHit`. Um hit pode gerar
`DocumentNavigationRequest` ou `EvidenceSourceCandidate`.

### 6.7 Evidências e navegação

```text
SearchHit ou página documental
  → EvidenceSourceCandidate
  → EvidenceController.start_create_from_source
  → EvidenceDraft
  → CreateEvidenceRequest
  → EvidenceService
  → SQLiteEvidenceRepository
  → evidences em database.db
```

Edição usa `UpdateEvidenceRequest`; exclusão e duplicidade têm confirmações. A
fonte pode ser reaberta por `DocumentNavigationRequest`, passando pelo
`ProjectController` até `DocumentsController`. O mesmo fluxo de navegação parte
da busca.

### 6.8 Fluxos RSC implementados

Casos de uso RSC criam `Activity`, projeto RSC e `FunctionalExercise` por
comandos, assemblers e portas, retornando DTOs. Há consulta de exercícios e
normalização de `FunctionalAssignmentEvidence`. Os repositórios concretos RSC
são em memória e esses serviços não aparecem na `ProjectSession` observada.

## 7. Classificação arquitetural de todos os arquivos

Somente as categorias solicitadas são utilizadas.

### UI

- `ui/main_window.py`, `ui/contribution_installer.py`, todos os arquivos de
  `ui/dialogs`, `ui/views` e `ui/widgets`: criam, compõem ou atualizam Qt.
- `ui/__init__.py` e `ui/constants/__init__.py`: fachadas/marcadores da UI.

### Application

- Todos os arquivos de `controllers`: coordenam UI e serviços.
- `core/project_controller.py`, `core/project_manager.py`: orquestram fluxos.
- `applications/rsc/application.py`, todos os `commands`, `dto`, `assemblers`,
  `services` e `queries/__init__.py`: fronteira e casos de uso RSC.
- `services/document_service.py`, `evidence_service.py`,
  `services/search_service.py`, `services/search/search_service.py`,
  `legacy_indexed_search_service.py`: serviços/fachadas.
- `services/indexing/document_indexer.py` e
  `services/processing/document_processor.py`: orquestradores.

### Domain

- `models/document.py`, `document_type.py`, `evidence.py`, `project.py`:
  entidades/valores centrais do host.
- Todos os arquivos de `applications/rsc/models`: domínio RSC.
- Arquivos em `applications/rsc/ports`: portas orientadas ao domínio.
- `services/evidence_repository_port.py`, `document_source_resolver.py`:
  portas de evidência/documento.
- `services/search/search_index.py`, `search_index_maintainer.py`,
  `search_index_source.py`: portas de busca.
- `services/processing/parsers/document_parser.py` e abstrações
  `OCREngine`/`PageClassificationStrategy`: contratos conceituais.

### Infrastructure

- Todos os arquivos de `database`: SQLite e migrations.
- `services/document_importer.py`, `document_repository.py`,
  `sqlite_evidence_repository.py`, `evidence_repository.py`,
  `evidence_repository_errors.py`, `search_document_source_resolver.py`.
- Adapters/repositories concretos de `services/processing`, `services/search`
  e `services/indexing`, exceto contratos/resultados/orquestradores já
  classificados.
- Todos os `applications/rsc/repositories`: adapters em memória.

### Shared/Core

- `app.py`; todos os arquivos de `core`, exceto controller/manager já
  classificados; todos os arquivos de `contracts`.
- `models/__init__.py`, read models, draft, requests, candidate e resultado de
  busca: objetos transversais.
- `__init__.py` de applications/services e subsistemas: fachadas.
- Resultados/contratos em `services/indexing/indexing_result.py`,
  `processing/processing_result.py`, `processing/ocr/ocr_result.py`,
  `search/contracts.py`, `search_filters.py`, `maintenance_contracts.py`,
  `search_result.py`.

### Unknown

- Todos os 45 arquivos de `tests`: verificação transversal, sem camada única.

Cada arquivo Python aparece nominalmente na seção 2; esta seção classifica por
conjuntos sem introduzir categorias adicionais. Documentos Markdown,
`requirements.txt` e licença não são módulos executáveis.

## 8. Avaliação objetiva da arquitetura atual

### Pontos bem estruturados

- Entrada pequena e composition root explícito.
- Lifetime de projeto encapsulado em `ProjectSession`.
- Registry e contrato de aplicações.
- Evidência imutável, requests, porta, serviço e adapter distintos.
- Busca com contratos, portas e adapters FTS.
- Processamento com parser abstrato, registry e OCR substituível.
- RSC dividido em comandos, DTOs, services, assemblers, models e ports.
- Migrations transacionais e persistências JSON por troca temporária.
- Muitos testes de caracterização e arquitetura estão presentes.

### Responsabilidades misturadas

- `ProjectController` combina projeto, dialogs, importação, processamento,
  navegação, mensagens e coordenação de controllers.
- `MainWindow` combina construção, navegação, estado de ações e apresentação.
- `EvidenceController` combina máquina de editor, serviço, confirmação, fonte
  e navegação.
- `DocumentIndexer` combina validação, tradução, manutenção e relatórios.
- `DocumentMetadataExtractor` concentra várias regras de reconhecimento.
- `Project` do host inclui modelo, serialização e I/O.
- `ocr_engine.py` contém abstração e adapter concreto.

### Componentes preparados para evolução

- Application registry/contributions, sessão de projeto, portas, parser
  registry, migrations e contratos versionados.
- Value objects imutáveis e estados explícitos no domínio RSC.
- Índice tratado como adapter e projeção reconstruível.
- Blueprint e ADRs registram componentes futuros sem classes atuais.

### Pontos que dificultam manutenção

- APIs legadas e atuais de busca coexistem.
- Duas classes `Project`, múltiplos `SearchResult` e duas
  `EvidenceNotFoundError`.
- Fachadas reexportam muitos símbolos.
- Core/controller depende diretamente de PySide6.
- Estado `.pdop` está distribuído entre JSON, SQLite e arquivos.
- RSC em memória não integra a sessão atual.
- Documentação futura e código legado representam estágios arquiteturais
  diferentes.
- O workspace auditado está sujo, com parte do RSC ainda não rastreada.

As observações acima não prescrevem alterações.

## 9. Estado do domínio

| Objeto | Regra/papel implementado | Relações |
|---|---|---|
| `models.Project` | Projeto físico versionado e associado a uma Application | Usado por manager, state, session e repositories |
| `Document` / `DocumentType` | Fonte importada, SHA, tipo e processamento | Catálogo, processor, UI e índice |
| `Evidence` | UUID, fonte, página, textos, datas e timestamps válidos | Service/repository/UI |
| Requests/Draft/Candidate | Entrada/edição/transição entre módulos | Search/Documents → Evidence |
| `Activity` | Atividade RSC mínima no estado inicial | Service/port/repository |
| `applications.rsc.models.Project` | Aggregate root RSC mínimo | Service/port/repository |
| `FunctionalExerciseId/Type/Role/Context/Period/Status` | Value objects e regras temporais | Compõem `FunctionalExercise` |
| `FunctionalExercise` | Exercício contínuo; coerência status-período e encerramento imutável | Assembler/service/repository/DTO |
| `FunctionalAssignmentEvidenceId`, `SourceEvidenceReference`, status | Identidade, fonte e etapa | Compõem atribuição |
| `FunctionalAssignmentEvidence` | Campos funcionais, datas e transições lineares | Assembler/Normalizer |
| `FunctionalAssignmentNormalizer` | Produz cópia normalizada preservando campos | Atua sobre atribuição RAW |
| Contratos de search | Queries, filtros, hits e paginação válidos | Service/index/UI |

Não existem classes atuais chamadas `IdentityProfile`, `EvidenceDiscovery`,
`IdentityResolver`, `FunctionalActivityResolver`, `ContinuityResolver` ou
`CareerTimeline`; são conceitos documentais.

## 10. Estado da interface

### Views

`HomeView`, `PdfView`, `SearchWorkspace`, `EvidenceWorkspace` e
`DocumentsWorkspace` residem no `QStackedWidget`; `BaseView` oferece ciclo
comum. `PdfView` cobre página, zoom e busca interna.

### Dialogs

`BaseDialog` e `NewProjectDialog`; também são usados diretamente `QFileDialog`,
`QMessageBox` e `QProgressDialog`.

### Widgets

- Projeto: `ProjectTreeWidget`.
- Busca: `SearchPanel`, `SearchResultsWidget`, `SearchPreviewWidget`.
- Evidência: `EvidenceListWidget`, `EvidenceEditorWidget`,
  `EvidenceSourceStatusWidget`.
- Documentos: `DocumentListWidget`, `DocumentMetadataWidget`,
  `DocumentPageListWidget`, `DocumentTextWidget`.

### Controllers

`ProjectController` é o mediador superior; `SearchController`,
`DocumentsController` e `EvidenceController` controlam seus workspaces e
comunicam-se indiretamente via callbacks do controller superior.

### Menus, toolbar e dock

Menus base: `file`, `edit`, `evidence`, `classification`, `tools`, `help`.
Aplicações podem contribuir ações e menus. A toolbar “Principal” expõe
projeto, importação, documentos, processamento, pesquisa e evidências. O
`QDockWidget` “Propriedades” fica à direita e mostra o documento selecionado.
A árvore do projeto integra o splitter central, não um dock.

```text
MainWindow
├── menus/toolbar → QAction → ProjectController
├── ProjectTreeWidget → ProjectController
├── stack
│   ├── SearchWorkspace ↔ SearchController
│   ├── DocumentsWorkspace ↔ DocumentsController
│   ├── EvidenceWorkspace ↔ EvidenceController
│   ├── PdfView ← ProjectController
│   └── HomeView
└── Properties Dock ← documento selecionado
```

## 11. Estado da persistência

### Formato `.pdop`

`.pdop` é uma pasta:

```text
<nome>.pdop/
├── project.json
├── database.db
├── documents.db.json       # após salvar catálogo
├── documents/
├── processing/             # criado sob demanda
│   └── <sha256>.json
├── cache/
├── exports/
├── logs/
└── temp/
```

### Criação e abertura

`ProjectManager.create_project` cria a pasta/subpastas, o modelo, o SQLite e
`project.json`, removendo a pasta parcial em falha. `open_project` exige
`project.json`, usa `Project.load`, atualiza `last_opened_at` e salva.

### `project.json`

Contém nome, timestamps, `application`, `format_version` e nome do banco.
`project_path` é reconstruído pela localização. `Project.save` usa arquivo
`.tmp` e replace.

### Documentos e processamento

`DocumentImporter` copia originais para `documents/`. `DocumentRepository`
grava `documents.db.json`. `ProcessingRepository` grava um JSON por SHA-256
com parser, versão, páginas, texto, metadados, OCR/status/erro.

### `database.db`

Schema atual 3: `documents`, `document_pages`, `document_pages_fts`,
`index_state`, `evidences`, índices auxiliares,
`search_index_documents` e `search_index_metadata`. `ProjectDatabase` controla
conexão/transação/migrations. Evidências usam `SQLiteEvidenceRepository`;
busca e manutenção usam adapters FTS distintos.

### Persistência RSC

Projetos RSC, atividades e exercícios usam somente repositórios em memória.
Eles não integram `ProjectSessionFactory`. Não foi encontrado adapter
persistente de `FunctionalAssignmentEvidence`.

## 12. Resumo executivo

| Componente | Responsabilidade | Camada | Estado atual | Observações |
|---|---|---|---|---|
| Bootstrap | Composição Qt | Shared/Core | Implementado | `app.py` → Application |
| MainWindow | Shell desktop | UI | Implementado | 584 linhas |
| ProjectController | Orquestração | Application | Implementado | 843 linhas |
| ProjectSession | Lifetime | Shared/Core | Implementado | Serviços por projeto |
| Registry/Contributions | Extensão por Application | Shared/Core/UI | Implementado | RSC registrado |
| Projeto `.pdop` | Unidade física | Domain/Infrastructure | Implementado | Pasta híbrida |
| Documentos | Importação/catálogo | Domain/Infrastructure | Implementado | Binário + JSON |
| Processamento/OCR | Extração | Application/Infrastructure | Implementado | PDF padrão |
| Pesquisa | FTS | Application/Infrastructure | Implementado | API atual + legada |
| Evidência | CRUD factual | Domain/Application/Infrastructure | Implementado | SQLite |
| RSC | Domínio/casos de uso | Domain/Application | Parcial | Repositórios em memória |
| FunctionalExercise | Exercício funcional | Domain | Implementado como modelo | Fora da sessão host |
| AssignmentEvidence/Normalizer | Pipeline inicial | Domain/Application | Presente não rastreado | Sem fluxo desktop |
| Identity Discovery/Resolution | Identidade | Domain | Somente documental | ADR-005/006 |
| Activity/Continuity Resolver | Reconstrução | Domain | Não implementado | ADRs futuros |
| CareerTimeline | Projeção | Domain | Somente documental | Sem classe |
| Testes | Caracterização | Unknown | 45 arquivos | Não executados |

## 13. Matriz preliminar de migração

| Componente | Classificação |
|---|---|
| Evidências e proveniência | provavelmente preservado |
| `FunctionalExercise` e value objects | provavelmente preservado |
| Documentos e dados `.pdop` existentes | provavelmente preservado |
| Contratos de Application e navegação | provavelmente preservado |
| Portas de evidência/search/RSC | provavelmente preservado |
| Migrations e versões persistidas | provavelmente preservado |
| ProjectSession/ApplicationRegistry | provavelmente preservado |
| ProjectController | requer análise posterior |
| MainWindow/controllers | requer análise posterior |
| APIs legadas de busca | requer análise posterior |
| Persistências JSON paralelas ao SQLite | requer análise posterior |
| DocumentIndexer/FTS maintainer | requer análise posterior |
| Repositórios RSC em memória | requer análise posterior |
| ContributionManager versus Installer | requer análise posterior |
| IdentityProfile/EvidenceDiscovery | situação ainda indefinida |
| IdentityResolver | situação ainda indefinida |
| FunctionalActivityResolver | situação ainda indefinida |
| ContinuityResolver | situação ainda indefinida |
| CareerTimeline | situação ainda indefinida |
| Persistência e integração RSC–host | situação ainda indefinida |

Esta matriz registra somente o grau de definição atual.

## 14. Perguntas arquiteturais

- Qual é a fronteira definitiva entre `ProjectController` e os três
  controllers de workspace?
- Qual é o papel vigente de `ContributionManager` diante de
  `DesktopContributionInstaller`?
- Qual dos contratos/resultados de pesquisa é a API pública definitiva?
- Qual é a finalidade residual dos serviços e modelos de busca legados?
- A classe `Project` RSC representa o mesmo conceito do projeto `.pdop` ou um
  agregado independente?
- Quais serviços RSC devem participar de uma sessão de projeto?
- Qual é a autoridade canônica sobre catálogo documental: JSON, tabelas
  SQLite ou resultados processados?
- Qual é a relação esperada entre `documents.db.json` e a tabela `documents`?
- Qual componente cria e mantém `processing/` durante todo o lifecycle?
- Qual é o objetivo atual de `DocumentClassifier`, dado o extractor de
  metadados e o parser?
- Qual é o estado contratual dos arquivos RSC ainda não rastreados?
- Como `FunctionalAssignmentEvidence` será ligada a `models.Evidence` além da
  referência opaca?
- Quais estados de identidade permitem prosseguir para atividade?
- Como decisões humanas de identidade serão representadas?
- Como a taxonomia funcional será armazenada e versionada?
- Como atividade e continuidade reagirão a revisão de identidade?
- Como `FunctionalExercise` será persistido no `.pdop`?
- Como a `CareerTimeline` será materializada/reconstruída?
- Quais documentos arquiteturais representam decisão vigente e quais são
  históricos?
- O arquivo textual residual na raiz pertence ao projeto ou é somente artefato
  de comando?
- Quais ações RSC serão expostas por `RscApplication.contributions()`?
- Quais critérios determinam quando adapters legados deixam de ser usados?

As perguntas registram incertezas observadas e permanecem sem resposta nesta
auditoria.
