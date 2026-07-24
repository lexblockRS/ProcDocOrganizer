import ast
from datetime import datetime
from pathlib import Path
import unittest
from uuid import uuid4

from models import (
    CreateEvidenceRequest,
    Evidence,
    EvidenceDraft,
    EvidenceSourceCandidate,
    UpdateEvidenceRequest,
)
from services import (
    DocumentSourceResolver,
    EvidenceRepository,
    SQLiteEvidenceRepository,
)
from services.evidence_repository import (
    EvidenceRepository as LegacyEvidenceRepository,
)


class EvidencePersistenceArchitectureTests(unittest.TestCase):
    def test_public_contracts_use_opaque_document_identity_fields(self):
        contracts = (
            Evidence,
            CreateEvidenceRequest,
            UpdateEvidenceRequest,
            EvidenceDraft,
            EvidenceSourceCandidate,
        )
        for contract in contracts:
            with self.subTest(contract=contract.__name__):
                fields = set(contract.__dataclass_fields__)
                self.assertIn("document_identity", fields)
                self.assertNotIn("document_sha256", fields)

        instant = datetime(2026, 1, 1).isoformat()
        for opaque in (
            "documento-interno-123",
            "urn:procdoc:document:abc",
        ):
            with self.subTest(identity=opaque):
                evidence = Evidence.create(
                    document_identity=opaque,
                    title="Título",
                    timestamp=instant,
                )
                create = CreateEvidenceRequest(opaque, "Título")
                update = UpdateEvidenceRequest(str(uuid4()), opaque, "Título")
                draft = EvidenceDraft(document_identity=opaque, title="Título")
                candidate = EvidenceSourceCandidate(opaque, 1)
                self.assertEqual(evidence.document_identity, opaque)
                self.assertEqual(create.document_identity, opaque)
                self.assertEqual(update.document_identity, opaque)
                self.assertEqual(draft.document_identity, opaque)
                self.assertEqual(candidate.document_identity, opaque)

    def test_upper_layers_do_not_expose_or_validate_sha_identity(self):
        root = Path(__file__).parents[1]
        paths = (
            "models/evidence.py",
            "models/evidence_draft.py",
            "models/evidence_requests.py",
            "models/evidence_source_candidate.py",
            "services/evidence_service.py",
            "services/evidence_repository_port.py",
            "services/document_source_resolver.py",
            "services/search/search_result.py",
        )
        for relative_path in paths:
            with self.subTest(path=relative_path):
                source = (root / relative_path).read_text(
                    encoding="utf-8"
                ).lower()
                self.assertNotIn("document_sha256", source)
                self.assertNotIn("sha256", source)
                self.assertNotIn("_sha256", source)

    def test_port_exposes_only_existing_canonical_operations(self):
        expected = {
            "add",
            "get_by_id",
            "list_all",
            "list_by_document",
            "update",
            "delete",
            "exists",
            "count",
        }
        operations = {
            name
            for name, value in EvidenceRepository.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        self.assertEqual(operations, expected)

    def test_document_source_resolver_has_one_responsibility(self):
        operations = {
            name
            for name, value in DocumentSourceResolver.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        self.assertEqual(operations, {"is_document_available"})

    def test_service_does_not_import_sqlite_adapter_or_sqlite(self):
        path = (
            Path(__file__).parents[1]
            / "services"
            / "evidence_service.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            f"{node.module or ''}.{alias.name}"
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        )
        self.assertFalse(any("sqlite" in item.lower() for item in imports))
        self.assertFalse(any(
            "sqlite_evidence_repository" in item.lower()
            for item in imports
        ))
        self.assertFalse(any(
            "search_document_source_resolver" in item.lower()
            for item in imports
        ))
        self.assertIn(
            "document_source_resolver.DocumentSourceResolver", imports
        )

    def test_repository_does_not_query_documents(self):
        source = (
            Path(__file__).parents[1]
            / "services"
            / "sqlite_evidence_repository.py"
        ).read_text(encoding="utf-8").lower()
        self.assertNotIn(" from documents", source)
        self.assertNotIn(" join documents", source)
        self.assertNotIn("is_document_available", source)

    def test_sqlite_adapter_maps_opaque_api_to_legacy_physical_column(self):
        source = (
            Path(__file__).parents[1]
            / "services"
            / "sqlite_evidence_repository.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"document_sha256"', source)
        self.assertIn('"document_identity": row["document_sha256"]', source)

    def test_public_port_and_legacy_concrete_imports_are_preserved(self):
        self.assertIsNot(EvidenceRepository, SQLiteEvidenceRepository)
        self.assertIs(LegacyEvidenceRepository, SQLiteEvidenceRepository)

    def test_session_factory_uses_sqlite_adapter(self):
        source = (
            Path(__file__).parents[1]
            / "core"
            / "project_session_factory.py"
        ).read_text(encoding="utf-8")
        self.assertIn("SQLiteEvidenceRepository(project)", source)
        self.assertIn("SearchDocumentSourceResolver(project)", source)


if __name__ == "__main__":
    unittest.main()
