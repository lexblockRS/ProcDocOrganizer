import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QToolBar,
)

from applications.rsc.application import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from models import DocumentProcessingStatus, DocumentType
from presentation import (
    NotificationLevel,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
)
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class DocumentWorkspaceImportIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.window = MainWindow()
        self.state = ProjectState()
        self.manager = ProjectManager()
        registry = ApplicationRegistry([RscApplication()])
        self.controller = ProjectController(
            window=self.window,
            manager=self.manager,
            state=self.state,
            contribution_installer=DesktopContributionInstaller(
                self.window
            ),
            session_factory=ProjectSessionFactory(registry),
            application_registry=registry,
        )
        self.notifications = []
        self.window.notification_center.subscribe(
            self.notifications.append
        )
        self.project_path = self._create_project()

    def tearDown(self):
        if self.state.has_project:
            self.controller.close_project()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temporary_directory.cleanup()

    def _create_project(self):
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_project_name.return_value = "Projeto"
        dialog.get_project_folder.return_value = self.root
        dialog.get_application_id.return_value = "rsc"
        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ):
            self.controller.new_project()
        return self.root / "Projeto.pdop"

    def _pdf(self, name, content=None):
        path = self.root / name
        path.write_bytes(content or f"%PDF-1.4 {name}".encode())
        return path

    def _choose(self, paths):
        return patch(
            "core.project_controller.QFileDialog.getOpenFileNames",
            return_value=([str(path) for path in paths], "Arquivos PDF"),
        )

    def _rows(self):
        tree = self.window.documents_workspace.document_list_widget.list_widget
        return [
            tuple(tree.item(row).text(column) for column in range(3))
            for row in range(tree.count())
        ]

    def test_workspace_uses_own_toolbar_and_exact_list_columns(self):
        workspace = self.window.documents_workspace
        self.assertIsInstance(workspace.toolbar, QToolBar)
        self.assertIn(workspace.import_action, workspace.toolbar.actions())
        header = workspace.document_list_widget.list_widget.headerItem()
        self.assertEqual(
            tuple(header.text(column) for column in range(3)),
            ("Nome", "Tipo", "Data de inclusão"),
        )

    def test_import_single_pdf_persists_copies_refreshes_and_notifies(self):
        source = self._pdf("Portaria.pdf")
        set_project = Mock()
        self.window.set_project = set_project
        with self._choose((source,)):
            self.window.documents_workspace.import_action.trigger()

        documents = self.controller.session.document_repository.list_documents()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].name, "Portaria.pdf")
        self.assertTrue(
            (self.project_path / documents[0].relative_path).is_file()
        )
        self.assertEqual(len(self._rows()), 1)
        self.assertEqual(self._rows()[0][0], "Portaria.pdf")
        self.assertTrue(self._rows()[0][2])
        set_project.assert_not_called()
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.SUCCESS,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Documento importado.",
        )

    def test_import_multiple_pdfs_updates_list_and_persistence(self):
        sources = (self._pdf("A.pdf"), self._pdf("B.pdf"))
        with self._choose(sources):
            self.controller.import_documents()

        self.assertEqual(
            {row[0] for row in self._rows()},
            {"A.pdf", "B.pdf"},
        )
        self.assertEqual(
            len(self.controller.session.document_repository.list_documents()),
            2,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "2 documentos importados.",
        )

    def test_cancel_and_failure_are_reported_without_catalog_changes(self):
        with self._choose(()):
            self.controller.import_documents()
        self.assertEqual(self._rows(), [])
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.INFO,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Importação cancelada.",
        )

        source = self._pdf("Falha.pdf")
        with (
            self._choose((source,)),
            patch.object(
                self.controller.session.document_import_service,
                "import_file",
                side_effect=OSError("falha simulada"),
            ),
        ):
            self.controller.import_documents()
        self.assertEqual(self._rows(), [])
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )
        self.assertIn("falha simulada", self.notifications[-1].message)

    def test_non_pdf_selection_is_rejected_before_import(self):
        source = self.root / "Notas.txt"
        source.write_text("conteúdo", encoding="utf-8")
        with self._choose((source,)):
            self.controller.import_documents()
        self.assertEqual(self._rows(), [])
        self.assertEqual(
            self.controller.session.document_repository.list_documents(),
            [],
        )
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Somente arquivos PDF podem ser importados.",
        )

    def test_imported_document_is_rebuilt_after_project_reopen(self):
        source = self._pdf("Persistente.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        original = self.controller.session.document_repository.list_documents()

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()

        reopened = self.controller.session.document_repository.list_documents()
        self.assertEqual(
            [(item.id, item.sha256, item.name) for item in reopened],
            [(item.id, item.sha256, item.name) for item in original],
        )
        self.assertEqual(len(self._rows()), 1)
        self.assertEqual(self._rows()[0][0], "Persistente.pdf")

    def test_selection_store_and_read_only_inspector_stay_synchronized(self):
        source = self._pdf("Inspecionado.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        document = self.controller.session.document_repository.list_documents()[0]
        tree = self.window.documents_workspace.document_list_widget.list_widget

        tree.setCurrentRow(0)
        self.app.processEvents()
        selection = self.window.selection_store.snapshot.selection
        self.assertIs(selection.identity.kind, SelectionKind.DOCUMENT)
        self.assertEqual(selection.identity.identifier, document.sha256)
        values = self.window.documents_workspace.metadata_widget.values
        self.assertEqual(values["name"].text(), document.name)
        self.assertEqual(values["path"].text(), document.relative_path)
        self.assertEqual(values["hash"].text(), document.sha256)
        self.assertEqual(values["imported"].text(), document.imported_at)

        self.window.documents_workspace.search_input.setText("sem resultado")
        self.app.processEvents()
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
        self.assertEqual(values["name"].text(), "Não informado")

        self.window.selection_store.clear()
        self.assertIsNone(
            self.controller.documents_controller.selected_identity
        )
        self.assertEqual(values["name"].text(), "Não informado")
        self.window.documents_workspace.search_input.clear()
        self.window.selection_store.select(
            SelectionContext(
                SelectionIdentity(
                    SelectionKind.DOCUMENT,
                    document.sha256,
                ),
                display_name=document.name,
            )
        )
        self.assertEqual(values["name"].text(), document.name)

    def test_open_and_ocr_actions_reuse_existing_integrations(self):
        source = self._pdf("Acoes.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.app.processEvents()

        with patch.object(self.window, "show_document") as show_document:
            workspace.open_action.trigger()
        show_document.assert_called_once()
        self.assertEqual(
            self.notifications[-1].message,
            "Documento aberto.",
        )

        def complete_processing():
            self.controller.selected_document.processing_status = (
                DocumentProcessingStatus.PROCESSED
            )

        with patch.object(
            self.controller,
            "process_document",
            side_effect=complete_processing,
        ) as process_document:
            workspace.ocr_action.trigger()
        process_document.assert_called_once()
        self.assertEqual(
            [item.message for item in self.notifications[-2:]],
            ["OCR iniciado.", "OCR concluído."],
        )

        def fail_processing():
            self.controller.selected_document.processing_status = (
                DocumentProcessingStatus.FAILED
            )

        with patch.object(
            self.controller,
            "process_document",
            side_effect=fail_processing,
        ):
            workspace.ocr_action.trigger()
        self.assertEqual(
            [item.message for item in self.notifications[-2:]],
            ["OCR iniciado.", "Não foi possível concluir o OCR."],
        )
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )

    def test_removal_confirmation_updates_all_state_and_persists(self):
        source = self._pdf("Removido.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.app.processEvents()
        document = self.controller.session.document_repository.list_documents()[0]
        stored_path = self.project_path / document.relative_path

        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            workspace.remove_action.trigger()
        self.assertEqual(
            self.controller.session.document_repository.list_documents(),
            [],
        )
        self.assertFalse(stored_path.exists())
        self.assertEqual(self._rows(), [])
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
        self.assertIsNone(workspace.details)
        self.assertEqual(
            self.notifications[-1].message,
            "Documento removido.",
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        self.assertEqual(
            self.controller.session.document_repository.list_documents(),
            [],
        )
        self.assertEqual(self._rows(), [])

    def test_removal_cancellation_preserves_document_and_notifies(self):
        source = self._pdf("Preservado.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.app.processEvents()

        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            workspace.remove_action.trigger()
        self.assertEqual(
            len(self.controller.session.document_repository.list_documents()),
            1,
        )
        self.assertEqual(len(self._rows()), 1)
        self.assertEqual(
            self.notifications[-1].message,
            "Remoção cancelada.",
        )

    def test_document_type_edit_save_cancel_and_reopen(self):
        source = self._pdf("Editavel.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.app.processEvents()
        document = self.controller.session.document_repository.list_documents()[0]
        protected = (
            document.id,
            document.sha256,
            document.relative_path,
            document.imported_at,
        )

        self.assertTrue(workspace.metadata_widget.begin_edit())
        workspace.metadata_widget.type_editor.setCurrentIndex(
            workspace.metadata_widget.type_editor.findData(
                DocumentType.PORTARIA.value
            )
        )
        self.assertTrue(workspace.has_unsaved_metadata)
        workspace.metadata_widget.save_button.click()
        updated = self.controller.session.document_repository.find_by_hash(
            document.sha256
        )
        self.assertEqual(
            updated.document_type,
            DocumentType.PORTARIA.value,
        )
        self.assertEqual(
            (
                updated.id,
                updated.sha256,
                updated.relative_path,
                updated.imported_at,
            ),
            protected,
        )
        self.assertEqual(self._rows()[0][1], "portaria")
        self.assertEqual(
            workspace.metadata_widget.values["type"].text(),
            "portaria",
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Metadados atualizados.",
        )

        workspace.metadata_widget.begin_edit()
        workspace.metadata_widget.type_editor.setCurrentIndex(
            workspace.metadata_widget.type_editor.findData(
                DocumentType.OFICIO.value
            )
        )
        workspace.metadata_widget.cancel_button.click()
        self.assertEqual(
            workspace.metadata_widget.values["type"].text(),
            "portaria",
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Alterações canceladas.",
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        reopened = self.controller.session.document_repository.find_by_hash(
            document.sha256
        )
        self.assertEqual(
            reopened.document_type,
            DocumentType.PORTARIA.value,
        )

    def test_metadata_failure_keeps_draft_and_reports_error(self):
        source = self._pdf("Falha-edicao.pdf")
        with self._choose((source,)):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.app.processEvents()
        workspace.metadata_widget.begin_edit()
        workspace.metadata_widget.type_editor.setCurrentIndex(
            workspace.metadata_widget.type_editor.findData(
                DocumentType.CERTIFICADO.value
            )
        )

        self.assertFalse(
            self.controller.documents_controller.save_metadata(
                "tipo-inexistente"
            )
        )
        self.assertIn(
            "tipo documental",
            workspace.metadata_widget.unsaved_label.text(),
        )
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )

        with patch.object(
            self.controller.session.document_metadata_service,
            "update_document_type",
            side_effect=RuntimeError("falha de persistência"),
        ):
            workspace.metadata_widget.save_button.click()
        self.assertTrue(workspace.metadata_widget.is_editing)
        self.assertTrue(workspace.has_unsaved_metadata)
        self.assertIn(
            "falha de persistência",
            workspace.metadata_widget.unsaved_label.text(),
        )
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )
        workspace.metadata_widget.cancel_button.click()

    def test_unsaved_edit_guards_selection_filter_refresh_and_close(self):
        sources = (self._pdf("A.pdf"), self._pdf("B.pdf"))
        with self._choose(sources):
            self.controller.import_documents()
        workspace = self.window.documents_workspace
        table = workspace.document_list_widget.list_widget
        table.setCurrentRow(0)
        self.app.processEvents()
        first_identity = (
            self.controller.documents_controller.selected_identity
        )
        workspace.metadata_widget.begin_edit()
        workspace.metadata_widget.type_editor.setCurrentIndex(
            workspace.metadata_widget.type_editor.findData(
                DocumentType.OFICIO.value
            )
        )

        with patch(
            "core.project_controller.QMessageBox.warning",
            return_value=QMessageBox.StandardButton.Cancel,
        ):
            table.setCurrentRow(1)
            workspace.search_input.setText("B.pdf")
            workspace.filter_combo.setCurrentIndex(
                workspace.filter_combo.findData("processed")
            )
            workspace.refresh_action.trigger()
            workspace.remove_action.trigger()
            self.controller.close_project()
        self.assertTrue(self.state.has_project)
        self.assertEqual(
            self.controller.documents_controller.selected_identity,
            first_identity,
        )
        self.assertEqual(workspace.search_input.text(), "")
        self.assertEqual(workspace.filter_combo.currentData(), "all")
        self.assertTrue(workspace.has_unsaved_metadata)
        self.assertEqual(
            len(self.controller.session.document_repository.list_documents()),
            2,
        )

        with patch(
            "core.project_controller.QMessageBox.warning",
            return_value=QMessageBox.StandardButton.Discard,
        ):
            table.setCurrentRow(1)
        self.assertFalse(workspace.metadata_widget.is_editing)
        self.assertNotEqual(
            self.controller.documents_controller.selected_identity,
            first_identity,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Alterações canceladas.",
        )


if __name__ == "__main__":
    unittest.main()
