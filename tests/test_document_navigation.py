from dataclasses import FrozenInstanceError
import unittest

from contracts import DocumentNavigationRequest


class DocumentNavigationRequestTests(unittest.TestCase):
    def test_contract_is_immutable_and_normalizes_identity(self):
        request = DocumentNavigationRequest("  opaque-id  ", 3)
        self.assertEqual(request.document_identity, "opaque-id")
        self.assertEqual(request.page_number, 3)
        with self.assertRaises(FrozenInstanceError):
            request.page_number = 4

    def test_page_is_optional(self):
        request = DocumentNavigationRequest("opaque-id")
        self.assertIsNone(request.page_number)

    def test_rejects_empty_identity_and_invalid_page(self):
        invalid = (
            lambda: DocumentNavigationRequest(""),
            lambda: DocumentNavigationRequest("   "),
            lambda: DocumentNavigationRequest("id", 0),
            lambda: DocumentNavigationRequest("id", -1),
            lambda: DocumentNavigationRequest("id", True),
            lambda: DocumentNavigationRequest("id", "1"),
        )
        for factory in invalid:
            with self.subTest(factory=factory), self.assertRaises(ValueError):
                factory()

    def test_contract_has_no_physical_or_module_specific_fields(self):
        fields = set(DocumentNavigationRequest.__dataclass_fields__)
        self.assertEqual(fields, {"document_identity", "page_number"})
        for forbidden in (
            "file_path", "pdf", "document", "search_hit",
            "widget", "callback",
        ):
            self.assertNotIn(forbidden, fields)


if __name__ == "__main__":
    unittest.main()
