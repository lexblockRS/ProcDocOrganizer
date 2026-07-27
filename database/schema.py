"""Definição do schema SQLite do ProcDoc Organizer."""

SUPPORTED_SCHEMA_VERSION = 7
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

MIGRATION_V4_STATEMENTS = (
    """CREATE TABLE rsc_functional_assignment_evidences (
        id TEXT PRIMARY KEY NOT NULL,
        insertion_order INTEGER NOT NULL UNIQUE CHECK(insertion_order > 0),
        person_id TEXT NOT NULL,
        source_evidence_reference TEXT NOT NULL,
        exercise_type_code TEXT NOT NULL,
        exercise_type_label TEXT NOT NULL,
        role TEXT NOT NULL,
        organization TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        unit TEXT,
        administrative_reference TEXT,
        status TEXT NOT NULL,
        CHECK(length(trim(person_id)) > 0),
        CHECK(length(trim(source_evidence_reference)) > 0),
        CHECK(length(trim(exercise_type_code)) > 0),
        CHECK(length(trim(exercise_type_label)) > 0),
        CHECK(length(trim(role)) > 0),
        CHECK(length(trim(organization)) > 0),
        CHECK(end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
        CHECK(status IN ('raw', 'normalized', 'identified', 'linked'))
    )""",
    "CREATE INDEX idx_rsc_assignment_evidences_source "
    "ON rsc_functional_assignment_evidences(source_evidence_reference)",
    "UPDATE index_state SET value = '4' WHERE key = 'schema_version'",
)

MIGRATION_V5_STATEMENTS = (
    """CREATE TABLE rsc_functional_exercises (
        id TEXT PRIMARY KEY NOT NULL,
        insertion_order INTEGER NOT NULL UNIQUE CHECK(insertion_order > 0),
        person_id TEXT NOT NULL,
        exercise_type_code TEXT NOT NULL,
        exercise_type_label TEXT NOT NULL,
        role TEXT NOT NULL,
        context_organization TEXT NOT NULL,
        context_unit TEXT,
        context_reference TEXT,
        start_date TEXT NOT NULL,
        end_date TEXT,
        status TEXT NOT NULL,
        CHECK(length(trim(person_id)) > 0),
        CHECK(length(trim(exercise_type_code)) > 0),
        CHECK(length(trim(exercise_type_label)) > 0),
        CHECK(length(trim(role)) > 0),
        CHECK(length(trim(context_organization)) > 0),
        CHECK(end_date IS NULL OR end_date >= start_date),
        CHECK(status IN ('active', 'ended'))
    )""",
    """CREATE TABLE rsc_functional_exercise_assignment_evidences (
        exercise_id TEXT NOT NULL,
        assignment_evidence_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
        PRIMARY KEY(exercise_id, ordinal),
        UNIQUE(exercise_id, assignment_evidence_id),
        FOREIGN KEY(exercise_id)
            REFERENCES rsc_functional_exercises(id) ON DELETE CASCADE,
        FOREIGN KEY(assignment_evidence_id)
            REFERENCES rsc_functional_assignment_evidences(id)
    )""",
    "CREATE INDEX idx_rsc_exercise_assignment_evidence "
    "ON rsc_functional_exercise_assignment_evidences"
    "(assignment_evidence_id)",
    "UPDATE index_state SET value = '5' WHERE key = 'schema_version'",
)

MIGRATION_V6_STATEMENTS = (
    """CREATE TABLE rsc_activities (
        activity_id TEXT PRIMARY KEY NOT NULL,
        insertion_order INTEGER NOT NULL UNIQUE CHECK(insertion_order > 0),
        description TEXT NOT NULL,
        state TEXT NOT NULL,
        CHECK(length(trim(activity_id)) > 0),
        CHECK(length(trim(description)) > 0),
        CHECK(state IN (
            'lembrada',
            'em_investigacao',
            'parcialmente_comprovada',
            'comprovada'
        ))
    )""",
    """CREATE TABLE rsc_activity_functional_assignment_evidences (
        activity_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
        PRIMARY KEY(activity_id, ordinal),
        UNIQUE(activity_id, evidence_id),
        FOREIGN KEY(activity_id)
            REFERENCES rsc_activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY(evidence_id)
            REFERENCES rsc_functional_assignment_evidences(id)
    )""",
    "CREATE INDEX idx_rsc_activity_assignment_evidence "
    "ON rsc_activity_functional_assignment_evidences(evidence_id)",
    """CREATE TABLE rsc_activity_functional_exercises (
        activity_id TEXT NOT NULL,
        exercise_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
        PRIMARY KEY(activity_id, ordinal),
        UNIQUE(activity_id, exercise_id),
        FOREIGN KEY(activity_id)
            REFERENCES rsc_activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY(exercise_id)
            REFERENCES rsc_functional_exercises(id)
    )""",
    "CREATE INDEX idx_rsc_activity_functional_exercise "
    "ON rsc_activity_functional_exercises(exercise_id)",
    "UPDATE index_state SET value = '6' WHERE key = 'schema_version'",
)

MIGRATION_V7_STATEMENTS = (
    "ALTER TABLE documents ADD COLUMN document_id TEXT",
    "ALTER TABLE documents ADD COLUMN stored_filename TEXT",
    "ALTER TABLE documents ADD COLUMN relative_path TEXT",
    "ALTER TABLE documents ADD COLUMN file_size INTEGER",
    "ALTER TABLE documents ADD COLUMN extension TEXT",
    "ALTER TABLE documents ADD COLUMN mime_type TEXT",
    "ALTER TABLE documents ADD COLUMN imported_at TEXT",
    "ALTER TABLE documents ADD COLUMN status TEXT",
    "CREATE UNIQUE INDEX idx_documents_document_id "
    "ON documents(document_id) WHERE document_id IS NOT NULL",
    "UPDATE index_state SET value = '7' WHERE key = 'schema_version'",
)
