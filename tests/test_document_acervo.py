from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from core.project_manager import ProjectManager
from models import DocumentStatus
from services import (
    DocumentImportService,
    DocumentRepository,
)


class DocumentAcervoTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.project = ProjectManager().create_project(
            "Acervo", self.root
        )
        self.repository = DocumentRepository(self.project)
        self.repository.load()
        self.service = DocumentImportService(
            self.project, self.repository
        )
        self.source = self.root / "Portaria original.txt"
        self.content = b"conteudo documental"
        self.source.write_bytes(self.content)

    def test_import_calculates_hash_copies_with_uuid_and_persists_fields(self):
        result = self.service.import_file(self.source)
        document = result.document

        self.assertFalse(result.is_duplicate)
        self.assertEqual(
            document.sha256, hashlib.sha256(self.content).hexdigest()
        )
        self.assertEqual(document.original_filename, self.source.name)
        self.assertNotEqual(document.stored_filename, self.source.name)
        self.assertEqual(document.extension, ".txt")
        self.assertEqual(document.file_size, len(self.content))
        self.assertEqual(document.status, DocumentStatus.IMPORTED)
        self.assertTrue(
            (self.project.project_path / document.relative_path).is_file()
        )
        self.assertEqual(
            DocumentRepository(self.project).find_by_id(document.id),
            document,
        )

    def test_duplicate_hash_returns_existing_without_second_copy(self):
        first = self.service.import_file(self.source)
        second_source = self.root / "Outro nome.txt"
        second_source.write_bytes(self.content)

        second = self.service.import_file(second_source)

        self.assertTrue(second.is_duplicate)
        self.assertEqual(second.document.id, first.document.id)
        self.assertEqual(len(self.repository.list_all()), 1)
        self.assertEqual(
            len(tuple((self.project.project_path / "documents").iterdir())),
            1,
        )

    def test_list_and_find_by_hash_survive_repository_reopening(self):
        imported = self.service.import_file(self.source).document

        reopened = DocumentRepository(self.project)
        reopened.load()

        self.assertEqual(reopened.list_all(), (imported,))
        self.assertEqual(
            reopened.find_by_hash(imported.sha256), imported
        )

    def test_remove_deletes_record_and_physical_file(self):
        imported = self.service.import_file(self.source).document
        stored_path = self.project.project_path / imported.relative_path

        self.assertTrue(self.service.remove(imported.id))

        self.assertFalse(stored_path.exists())
        self.assertIsNone(self.repository.find_by_id(imported.id))
        self.assertEqual(self.repository.list_all(), ())
        self.assertFalse(self.service.remove(imported.id))

    def test_repository_update_preserves_identity(self):
        imported = self.service.import_file(self.source).document
        imported.original_filename = "Nome corrigido.txt"
        imported.name = imported.original_filename

        self.repository.update(imported)

        self.assertEqual(
            self.repository.find_by_id(imported.id).original_filename,
            "Nome corrigido.txt",
        )


if __name__ == "__main__":
    unittest.main()
