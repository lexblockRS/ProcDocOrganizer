from dataclasses import FrozenInstanceError
import unittest

from models import EvidenceDraft, EvidenceSourceCandidate
from services.search import SearchHit, SearchResult


SHA = "a" * 64


class EvidenceSourceCandidateTests(unittest.TestCase):
    def result(self, **changes):
        values = {
            "document_sha256": SHA,
            "document_title": "Portaria 123/2022",
            "page_number": 6,
            "snippet": "Trecho encontrado",
            "score": -1.0,
            "document_date": "2022-01-01",
            "document_type": "portaria",
            "file_path": "documents/portaria-123.pdf",
            "matched_terms": ("comissão",),
        }
        values.update(changes)
        return SearchResult(**values)

    def test_candidate_is_immutable_and_preserves_page_sha_snippet(self):
        candidate = EvidenceSourceCandidate.from_search_result(self.result())
        self.assertEqual(candidate.document_identity, SHA)
        self.assertEqual(candidate.page_number, 6)
        self.assertEqual(candidate.source_snippet, "Trecho encontrado")
        self.assertEqual(candidate.search_term, "comissão")
        with self.assertRaises(FrozenInstanceError):
            candidate.page_number = 7

    def test_search_hit_is_adapted_without_legacy_or_physical_fields(self):
        hit = SearchHit(
            document_identity=SHA,
            document_name="Portaria 123/2022",
            page_number=6,
            snippet="Trecho encontrado",
            score=1.0,
        )
        candidate = EvidenceSourceCandidate.from_search_hit(hit)
        self.assertEqual(candidate.document_identity, SHA)
        self.assertEqual(candidate.document_sha256, SHA)
        self.assertEqual(candidate.document_name, "Portaria 123/2022")
        self.assertEqual(candidate.page_number, 6)
        self.assertEqual(candidate.source_snippet, "Trecho encontrado")
        self.assertIsNone(candidate.document_path)
        self.assertIsNone(candidate.document_type)
        self.assertIsNone(candidate.search_term)

    def test_page_can_be_none(self):
        candidate = EvidenceSourceCandidate(
            SHA, None, "Conteúdo não paginado"
        )
        self.assertIsNone(candidate.page_number)

    def test_title_prefers_document_then_filename_then_type_and_snippet(self):
        cases = (
            (dict(), "Portaria 123/2022"),
            (dict(document_title=None), "portaria-123"),
            (dict(document_title=None, file_path=None), "portaria"),
            (dict(document_title=None, file_path=None, document_type=None,
                  snippet="  Primeira linha útil  \nsegunda"), "Primeira linha útil"),
            (dict(document_title=None, file_path=None, document_type=None,
                  snippet=""), "Evidência da pesquisa"),
        )
        for changes, expected in cases:
            with self.subTest(expected=expected):
                candidate = EvidenceSourceCandidate.from_search_result(
                    self.result(**changes)
                )
                self.assertEqual(candidate.suggested_title, expected)

    def test_normalizes_spaces_controls_and_keeps_useful_lines(self):
        candidate = EvidenceSourceCandidate(
            SHA.upper(), 1, "  linha   um\x00\n linha   dois  ",
            document_name="  Documento   oficial  ",
        )
        self.assertEqual(candidate.document_identity, SHA.upper())
        self.assertEqual(candidate.document_sha256, SHA.upper())
        self.assertEqual(candidate.document_name, "Documento oficial")
        self.assertEqual(candidate.source_snippet, "linha um\nlinha dois")

    def test_draft_has_only_source_fields_prefilled(self):
        candidate = EvidenceSourceCandidate.from_search_result(self.result())
        draft = EvidenceDraft.from_source_candidate(candidate)
        self.assertIsNone(draft.evidence_id)
        self.assertEqual(draft.document_sha256, SHA)
        self.assertEqual(draft.page_number, 6)
        self.assertEqual(draft.source_snippet, "Trecho encontrado")
        self.assertEqual(draft.title, "Portaria 123/2022")
        self.assertEqual(draft.category, "")
        self.assertEqual(draft.user_notes, "")
        self.assertEqual(draft.start_date, "")
        self.assertEqual(draft.end_date, "")

    def test_title_is_limited_and_sha_is_never_title_fallback(self):
        long_title = "x" * 400
        candidate = EvidenceSourceCandidate.from_search_result(
            self.result(document_title=long_title)
        )
        self.assertEqual(len(candidate.suggested_title), 300)
        fallback = EvidenceSourceCandidate.from_search_result(
            self.result(document_title=None, file_path=None,
                        document_type=None, snippet="")
        )
        self.assertNotIn(SHA, fallback.suggested_title)

    def test_document_path_preserves_internal_spaces_slashes_and_unicode(self):
        paths = (
            r"C:\Meu  Projeto\Documento.pdf",
            r"C:\Projetos\Pasta   com espaços\Documento.pdf",
            "/dados/Meu  Projeto/Documento.pdf",
            "/dados/Comissão Acadêmica/portaria.pdf",
            "documents/Meu  Documento.pdf",
        )
        for path in paths:
            with self.subTest(path=path):
                candidate = EvidenceSourceCandidate(SHA, 1, document_path=path)
                self.assertEqual(candidate.document_path, path)

    def test_document_path_has_own_control_character_normalization(self):
        candidate = EvidenceSourceCandidate(
            SHA, 1, document_path="  C:\\Meu  Projeto\n\\Documento\t.pdf  "
        )
        self.assertEqual(
            candidate.document_path, r"C:\Meu  Projeto\Documento.pdf"
        )
        self.assertIsNone(
            EvidenceSourceCandidate(SHA, 1, document_path=None).document_path
        )
        self.assertIsNone(
            EvidenceSourceCandidate(SHA, 1, document_path="  ").document_path
        )

    def test_search_result_path_is_preserved_and_not_copied_to_draft(self):
        path = r"C:\Meu  Projeto\Documento.pdf"
        candidate = EvidenceSourceCandidate.from_search_result(
            self.result(file_path=path)
        )
        draft = EvidenceDraft.from_source_candidate(candidate)
        self.assertEqual(candidate.document_path, path)
        self.assertFalse(hasattr(draft, "document_path"))


if __name__ == "__main__":
    unittest.main()
