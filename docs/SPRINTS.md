# ProcDocOrganizer Development Roadmap

---

# Sprint 1

Infrastructure

Status: ✅ Completed

Implemented:

- Project model
- Persistence
- Repositories
- Basic UI
- Document import

---

# Sprint 2

Document Manager

Status: ✅ Completed

Objective

Transform the application into a complete document management system.

Tasks

- [x] Extend Document model
- [x] Add page count
- [x] Add SHA256 hash
- [x] Add document status
- [x] Update DocumentRepository
- [x] Update ProjectController
- [x] Improve MainWindow document list
- [x] Add document properties panel
- [x] Add "Process Document" action
- [x] Preserve backward compatibility

Acceptance Criteria

- Project compiles
- Existing projects still open
- Document import works
- No regression

---

# Sprint 3

PDF Viewer

Status: 🚧 In Progress

Tasks

- [x] Integrated PDF viewer
- [x] Page navigation
- [x] Zoom
- [x] Search inside PDF
- [ ] Future support for highlighting excerpts

---

# Sprint 3.5

Processing Infrastructure

Status: ✅ Completed

Implemented:

- Processing service package
- Basic document processor
- Document type infrastructure
- Processing metadata persistence
- Backward compatibility for existing documents

---

# Sprint 4.1

Native PDF Text Extraction

Status: ✅ Completed

Implemented:

- Native PDF text extraction by page
- Processing result persistence by SHA-256
- Reuse of valid existing processing results
- Processing status and error persistence

---

# Sprint 4.2

Batch Document Processing

Status: ✅ Completed

Implemented:

- Sequential processing of pending documents
- Configurable batch limit with an initial limit of 100 documents
- Progress display and safe cancellation between documents
- Immediate persistence after each document
- Reuse of valid results with unchanged SHA-256
- Individual failure handling without stopping the batch

---

# Sprint 4

Document Processing

Status: Planned

Tasks

- [ ] Extract text
- [ ] OCR fallback
- [ ] Detect document type
- [ ] Store extracted text
- [ ] Build search index

---

# Sprint 5

Textual Search in Processed Documents

Status: ✅ Completed

Implemented:

- Search based exclusively on persisted processing JSON files
- Case-insensitive search for words and expressions
- Results with document, page and excerpt
- Open document and navigate to the matching page

No OCR, AI, inverted index or database was added.

Native extraction identifies documents without searchable text as
`ocr_required`, without performing OCR.

---

# Sprint 6

Document Enrichment

Status: ✅ Completed

Implemented:

- Deterministic metadata extraction from persisted native text
- Processing JSON enrichment with metadata extractor versioning
- Heuristics for title, document type, number, date, issuer and SEI fields
- Backward compatibility with existing processing results

---

# Sprint 7

## Sprint 7.1 - Banco e Indexador

Status: Implementado

- SQLite por projeto com schema versionado por `PRAGMA user_version`
- Índice textual por página usando FTS5 e normalização de diacríticos
- Indexação transacional e idempotente dos JSONs de processamento
- Reconstrução incremental e reconstrução completa explícita
- Sem alteração da busca visual homologada nos Sprints 5 e 6
- Integração automática adiada até a implementação do OCR

### Limitações

- FTS5 deve estar disponível no SQLite incluído no runtime Python.
- Ainda não existe `SearchService` baseado no novo índice.
- O indexador é acionado apenas programaticamente nesta etapa.

---

## Sprint 7.2 - OCR por página

Status: Implementado

- Classificação independente de cada página por estratégia configurável
- Preservação do texto nativo quando suficiente
- OCR encapsulado por `OCREngine`, com implementação Tesseract CLI
- Mesclagem transparente de documentos nativos, digitalizados e mistos
- Campos aditivos `text_source` e `ocr_used` no JSON
- Compatibilidade de leitura e reconstrução com `ocr_required` antigo

O motor concreto requer o executável Tesseract e o idioma `por` instalados no
sistema. Sua indisponibilidade é registrada como falha OCR por página, sem
acoplamento do restante do pipeline ao executável.

---

Timeline

Status: Planned

Tasks

- [ ] Chronological organization
- [ ] Filters
- [ ] Categories
- [ ] Search

---

# Sprint 8

Export

Status: Planned

Tasks

- [ ] Export to DOCX
- [ ] Export to PDF
- [ ] Export to Excel
- [ ] Structured report

---

# Development Rules

Every sprint must:

- compile successfully;
- preserve existing functionality;
- avoid unnecessary refactoring;
- include code cleanup where appropriate;
- update documentation when architecture changes.

Before implementing a sprint, always review:

- architecture_guidelines.md
- current sprint objectives
- existing codebase

Do not implement future sprints in advance.

Focus only on the current sprint.
