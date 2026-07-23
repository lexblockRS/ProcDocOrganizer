"""Definição do schema SQLite do ProcDoc Organizer."""

SUPPORTED_SCHEMA_VERSION = 3
INDEX_VERSION = 2

MIGRATION_V1_STATEMENTS = (
    """CREATE TABLE documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sha256 TEXT NOT NULL UNIQUE,
        original_filename TEXT,
        stored_path TEXT,
        processing_status TEXT NOT NULL,
        page_count INTEGER NOT NULL DEFAULT 0,
        title TEXT,
        document_type TEXT,
        document_number TEXT,
        document_date TEXT,
        issuing_organization TEXT,
        sei_process_number TEXT,
        sei_code TEXT,
        indexed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE document_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
        UNIQUE(document_id, page_number)
    )""",
    """CREATE VIRTUAL TABLE document_pages_fts USING fts5(
        text,
        -- Campos auxiliares: localizam o resultado, mas não são pesquisáveis.
        document_id UNINDEXED,
        page_number UNINDEXED,
        tokenize = 'unicode61 remove_diacritics 2'
    )""",
    "CREATE TABLE index_state (key TEXT PRIMARY KEY, value TEXT)",
    "INSERT INTO index_state(key, value) VALUES ('schema_version', '1')",
    "INSERT INTO index_state(key, value) VALUES ('index_version', '1')",
)

MIGRATION_V2_STATEMENTS = (
    """CREATE TABLE evidences (
        id TEXT PRIMARY KEY,
        document_sha256 TEXT NOT NULL,
        page_number INTEGER,
        title TEXT NOT NULL,
        source_snippet TEXT,
        user_notes TEXT,
        category TEXT,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK(page_number IS NULL OR page_number >= 1),
        CHECK(length(trim(title)) > 0),
        CHECK(length(document_sha256) = 64),
        CHECK(end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
    )""",
    "CREATE INDEX idx_evidences_document_sha256 ON evidences(document_sha256)",
    "CREATE INDEX idx_evidences_start_date ON evidences(start_date)",
    "UPDATE index_state SET value = '2' WHERE key = 'schema_version'",
)

MIGRATION_V3_STATEMENTS = (
    """CREATE TABLE search_index_documents (
        document_identity TEXT PRIMARY KEY,
        fingerprint TEXT NOT NULL,
        page_count INTEGER NOT NULL,
        indexed_at TEXT NOT NULL
    )""",
    """CREATE TABLE search_index_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
    "UPDATE index_state SET value = '2' WHERE key = 'index_version'",
    "UPDATE index_state SET value = '3' WHERE key = 'schema_version'",
)
