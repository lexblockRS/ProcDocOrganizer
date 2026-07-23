import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock
from uuid import UUID, uuid4

from database import ProjectDatabase, SUPPORTED_SCHEMA_VERSION, get_schema_version
from models import CreateEvidenceRequest, UpdateEvidenceRequest
from services.evidence_repository import EvidenceRepository, EvidenceRepositoryError
from services.search_document_source_resolver import SearchDocumentSourceResolver
from services.evidence_service import (
    EvidenceClockError,
    EvidenceDocumentUnavailableError,
    EvidenceNotFoundError,
    EvidenceService,
    EvidenceServiceError,
    EvidenceSourceStatus,
    EvidenceValidationError,
)
from services.indexing import DocumentIndexer
from services.search import (
    LegacyIndexedSearchService,
    SearchFilters,
    SqliteFtsSearchIndex,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
ID_A = "11111111-1111-4111-8111-111111111111"
CREATED = "2026-01-10T10:00:00"
UPDATED = "2026-01-11T11:00:00"


class EvidenceServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "database.db"
        self.processing = self.root / "processing"
        self.processing.mkdir()
        self.indexer = DocumentIndexer(self.database_path)
        self._index(SHA_A, "documento a", "termo pesquisável", "a.json")
        self._index(SHA_B, "documento b", "outro texto", "b.json")
        self.repository = EvidenceRepository(self.database_path)
        self.resolver = SearchDocumentSourceResolver(self.database_path)
        self.service = EvidenceService(
            self.repository,
            self.resolver,
            id_factory=lambda: ID_A,
            now_factory=lambda: CREATED,
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _index(self, sha, title, text, name):
        path = self.processing / name
        path.write_text(json.dumps({
            "document_sha256": sha, "processed_at": CREATED,
            "status": "processed", "page_count": 1,
            "pages": [{"page": 1, "text": text}],
            "metadata": {"title": title},
        }), encoding="utf-8")
        self.indexer.index_processing_result(path)

    def request(self, **changes):
        values = {
            "document_sha256": SHA_A,
            "page_number": 3,
            "title": "Participação em comissão",
            "source_snippet": "designar o servidor",
            "user_notes": "Atuação institucional",
            "category": None,
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
        }
        values.update(changes)
        return CreateEvidenceRequest(**values)

    def update_request(self, evidence, **changes):
        values = {
            "evidence_id": evidence.id,
            "document_sha256": evidence.document_sha256,
            "page_number": evidence.page_number,
            "title": evidence.title,
            "source_snippet": evidence.source_snippet,
            "user_notes": evidence.user_notes,
            "category": evidence.category,
            "start_date": evidence.start_date,
            "end_date": evidence.end_date,
        }
        values.update(changes)
        return UpdateEvidenceRequest(**values)

    def test_create_generates_id_and_both_timestamps(self):
        evidence = self.service.create(self.request())
        self.assertEqual(evidence.id, ID_A)
        self.assertEqual(evidence.created_at, CREATED)
        self.assertEqual(evidence.updated_at, CREATED)
        self.assertEqual(self.repository.get_by_id(ID_A), evidence)

    def test_default_id_factory_generates_uuid(self):
        evidence = EvidenceService(
            self.repository, self.resolver, now_factory=lambda: CREATED
        ).create(self.request())
        self.assertEqual(str(UUID(evidence.id)), evidence.id)

    def test_create_with_optional_fields(self):
        evidence = self.service.create(self.request(
            page_number=None, source_snippet=None, user_notes=" ", category=None,
            start_date=None, end_date=None,
        ))
        self.assertIsNone(evidence.page_number)
        self.assertIsNone(evidence.user_notes)

    def test_requests_are_immutable_and_normalized(self):
        request = self.request(title="  Título  ", source_snippet=" ")
        self.assertEqual(request.title, "Título")
        self.assertIsNone(request.source_snippet)
        with self.assertRaises(FrozenInstanceError):
            request.title = "Outro"

    def test_invalid_request_fields_are_rejected_before_persistence(self):
        invalid = (
            lambda: self.request(document_identity=""),
            lambda: self.request(title=" "),
            lambda: self.request(page_number=0),
            lambda: self.request(start_date="2024-01-02", end_date="2024-01-01"),
        )
        for factory in invalid:
            with self.subTest(factory=factory), self.assertRaises(ValueError):
                factory()
        self.assertEqual(self.repository.count(), 0)

    def test_create_for_missing_document_has_service_error(self):
        with self.assertRaises(EvidenceDocumentUnavailableError) as caught:
            self.service.create(self.request(document_sha256="c" * 64))
        self.assertIsNotNone(caught.exception.__cause__)

    def test_duplicate_factory_id_is_mapped(self):
        self.service.create(self.request())
        with self.assertRaises(EvidenceValidationError) as caught:
            self.service.create(self.request(title="Outra"))
        self.assertIsNotNone(caught.exception.__cause__)

    def test_get_and_get_required(self):
        evidence = self.service.create(self.request())
        self.assertEqual(self.service.get(evidence.id), evidence)
        self.assertEqual(self.service.get_required(evidence.id), evidence)
        self.assertIsNone(self.service.get(str(uuid4())))

    def test_get_required_missing_raises(self):
        with self.assertRaises(EvidenceNotFoundError):
            self.service.get_required(str(uuid4()))

    def test_lists_return_tuples_and_preserve_repository_order(self):
        ids = iter((ID_A, "22222222-2222-4222-8222-222222222222"))
        service = EvidenceService(
            self.repository, self.resolver,
            id_factory=lambda: next(ids), now_factory=lambda: CREATED
        )
        later = service.create(self.request(title="B", start_date="2024-01-01", end_date=None))
        earlier = service.create(self.request(title="A", start_date="2023-01-01", end_date=None))
        self.assertIsInstance(service.list_all(), tuple)
        self.assertEqual(service.list_all(), (earlier, later))
        self.assertIsInstance(service.list_by_document(SHA_A), tuple)

    def test_update_preserves_id_and_created_and_changes_updated(self):
        evidence = self.service.create(self.request())
        service = EvidenceService(
            self.repository, self.resolver, now_factory=lambda: UPDATED
        )
        updated = service.update(self.update_request(evidence, title="Título novo"))
        self.assertEqual(updated.id, evidence.id)
        self.assertEqual(updated.created_at, evidence.created_at)
        self.assertEqual(updated.updated_at, UPDATED)
        self.assertEqual(updated.title, "Título novo")

    def test_update_can_change_document_link(self):
        evidence = self.service.create(self.request())
        service = EvidenceService(
            self.repository, self.resolver, now_factory=lambda: UPDATED
        )
        updated = service.update(self.update_request(evidence, document_sha256=SHA_B))
        self.assertEqual(updated.document_sha256, SHA_B)

    def test_update_to_missing_document_is_mapped(self):
        evidence = self.service.create(self.request())
        service = EvidenceService(
            self.repository, self.resolver, now_factory=lambda: UPDATED
        )
        with self.assertRaises(EvidenceDocumentUnavailableError):
            service.update(self.update_request(evidence, document_sha256="c" * 64))

    def test_update_missing_evidence_is_rejected(self):
        request = UpdateEvidenceRequest(
            evidence_id=str(uuid4()), document_sha256=SHA_A, title="Ausente"
        )
        with self.assertRaises(EvidenceNotFoundError):
            self.service.update(request)

    def test_regressing_clock_is_rejected(self):
        evidence = self.service.create(self.request())
        service = EvidenceService(
            self.repository, self.resolver,
            now_factory=lambda: "2025-01-01T00:00:00"
        )
        with self.assertRaises(EvidenceClockError):
            service.update(self.update_request(evidence))

    def test_delete_is_idempotent_exists_and_count(self):
        evidence = self.service.create(self.request())
        self.assertTrue(self.service.exists(evidence.id))
        self.assertEqual(self.service.count(), 1)
        self.assertTrue(self.service.delete(evidence.id))
        self.assertFalse(self.service.delete(evidence.id))
        self.assertFalse(self.service.exists(evidence.id))
        self.assertEqual(self.service.count(), 0)

    def test_source_status_tracks_index_without_persistence(self):
        evidence = self.service.create(self.request())
        self.assertEqual(
            self.service.get_source_status(evidence.id), EvidenceSourceStatus.AVAILABLE
        )
        self.assertTrue(self.service.is_source_available(evidence))
        self.indexer.remove_document(SHA_A)
        self.assertEqual(
            self.service.get_source_status(evidence.id), EvidenceSourceStatus.UNAVAILABLE
        )
        self.assertFalse(self.service.is_source_available(evidence.id))
        self._index(SHA_A, "documento a", "termo pesquisável", "a.json")
        self.assertEqual(
            self.service.get_source_status(evidence.id), EvidenceSourceStatus.AVAILABLE
        )

    def test_find_duplicates_uses_document_page_and_casefolded_title(self):
        evidence = self.service.create(self.request(title="  Comissão Especial "))
        matches = self.service.find_potential_duplicates(
            SHA_A, 3, "comissão especial"
        )
        self.assertEqual(matches, (evidence,))
        self.assertEqual(
            self.service.find_potential_duplicates(SHA_A, 2, "Comissão Especial"), ()
        )
        self.assertEqual(
            self.service.find_potential_duplicates(SHA_A, 3, "Título diferente"), ()
        )

    def test_find_duplicates_supports_null_page(self):
        evidence = self.service.create(self.request(page_number=None))
        self.assertEqual(
            self.service.find_potential_duplicates(SHA_A, None, evidence.title),
            (evidence,),
        )

    def test_technical_repository_error_is_mapped_without_leaking_details(self):
        repository = Mock()
        technical = EvidenceRepositoryError("SELECT segredo FROM evidences")
        repository.list_all.side_effect = technical
        service = EvidenceService(repository, Mock())
        with self.assertRaises(EvidenceServiceError) as caught:
            service.list_all()
        self.assertNotIn("SELECT", str(caught.exception))
        self.assertIs(caught.exception.__cause__, technical)

    def test_schema_remains_current_and_search_stays_functional(self):
        with ProjectDatabase(self.database_path) as database:
            self.assertEqual(
                get_schema_version(database.connection),
                SUPPORTED_SCHEMA_VERSION,
            )
        results = LegacyIndexedSearchService(
            SqliteFtsSearchIndex(self.database_path)
        ).search(
            SearchFilters(terms=["pesquisavel"])
        )
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
