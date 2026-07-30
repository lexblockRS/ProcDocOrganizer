from pathlib import Path
import unittest
from unittest.mock import Mock

from models import Document, DocumentType
from services import (
    DocumentMetadataError,
    DocumentMetadataService,
)


class DocumentMetadataServiceTests(unittest.TestCase):
    def setUp(self):
        self.document = Document.create(
            name="Documento.pdf",
            relative_path="documents/arquivo.pdf",
            sha256="a" * 64,
            document_type=DocumentType.UNKNOWN.value,
        )
        self.repository = Mock()
        self.repository.find_by_hash.return_value = self.document
        self.service = DocumentMetadataService(self.repository)

    def test_only_existing_document_type_is_updated(self):
        protected = (
            self.document.id,
            self.document.sha256,
            self.document.relative_path,
            self.document.imported_at,
            self.document.original_filename,
        )
        result = self.service.update_document_type(
            self.document.sha256,
            DocumentType.PORTARIA.value,
        )
        self.assertIs(result, self.document)
        self.assertEqual(
            self.document.document_type,
            DocumentType.PORTARIA.value,
        )
        self.assertEqual(
            (
                self.document.id,
                self.document.sha256,
                self.document.relative_path,
                self.document.imported_at,
                self.document.original_filename,
            ),
            protected,
        )
        self.repository.update.assert_called_once_with(self.document)

    def test_invalid_type_and_missing_document_are_rejected(self):
        with self.assertRaisesRegex(
            DocumentMetadataError,
            "tipo documental",
        ):
            self.service.update_document_type(
                self.document.sha256,
                "categoria-inventada",
            )
        self.repository.update.assert_not_called()

        self.repository.find_by_hash.return_value = None
        with self.assertRaisesRegex(
            DocumentMetadataError,
            "não foi localizado",
        ):
            self.service.update_document_type(
                "b" * 64,
                DocumentType.OFICIO.value,
            )

    def test_repository_failure_is_propagated_without_technical_mutation(self):
        self.repository.update.side_effect = RuntimeError("SQLite indisponível")
        with self.assertRaisesRegex(RuntimeError, "SQLite"):
            self.service.update_document_type(
                self.document.sha256,
                DocumentType.CERTIFICADO.value,
            )
        self.assertEqual(self.document.id, self.document.id)
        self.assertEqual(self.document.sha256, "a" * 64)
        self.assertEqual(
            self.document.relative_path,
            "documents/arquivo.pdf",
        )


class DocumentMetadataArchitectureTests(unittest.TestCase):
    def test_no_new_organizational_domain_concepts_are_declared(self):
        protected_names = {
            "Category",
            "DocumentTag",
            "FavoriteDocument",
            "DocumentObservation",
        }
        roots = (Path("models"), Path("services"), Path("controllers"))
        declared = set()
        import ast

        for root in roots:
            for path in root.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                declared.update(
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                )
        self.assertTrue(protected_names.isdisjoint(declared))


if __name__ == "__main__":
    unittest.main()
