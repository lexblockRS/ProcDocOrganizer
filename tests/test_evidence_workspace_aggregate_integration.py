import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog

from applications.rsc.application import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from core.application_lifecycle_host import ApplicationLifecycleHost
from models import EvidenceDraft
from presentation import NotificationLevel, SelectionKind
from services import EvidenceManagementService, EvidenceServiceError
from services.processing import ProcessingRepository, ProcessingResult
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class EvidenceWorkspaceAggregateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.window = MainWindow()
        self.lifecycle_host = ApplicationLifecycleHost()
        self.state = ProjectState(self.lifecycle_host)
        registry = ApplicationRegistry([RscApplication()])
        self.controller = ProjectController(
            window=self.window,
            manager=ProjectManager(),
            state=self.state,
            lifecycle_host=self.lifecycle_host,
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
        self.document = self._import_document()
        ProcessingRepository(
            self.controller.session.project
        ).save(ProcessingResult(
            document_sha256=self.document.sha256,
            processed_at="2026-01-01T10:00:00",
            status="processed",
            page_count=1,
            pages=[{
                "page": 1,
                "text": "Designar a comissão.",
            }],
        ))
        self.controller.show_evidences()

    def tearDown(self):
        if self.state.has_project:
            if self.controller.evidence_controller.dirty:
                self.controller.evidence_controller.cancel()
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

    def _import_document(self):
        source = self.root / "Portaria.pdf"
        source.write_bytes(b"%PDF-1.4 Evidence Workspace")
        with patch(
            "core.project_controller.QFileDialog.getOpenFileNames",
            return_value=([str(source)], "Arquivos PDF"),
        ):
            self.controller.import_documents()
        return (
            self.controller.session.document_repository
            .list_documents()[0]
        )

    def _create_evidence(self):
        controller = self.controller.evidence_controller
        controller.start_create()
        controller.update_draft(EvidenceDraft(
            document_identity=self.document.sha256,
            page_number=1,
            title="Portaria de coordenação",
            source_snippet="Designar a comissão.",
            user_notes="Conferir período.",
            category="Gestão",
            start_date="2024-01-01",
            end_date="2024-12-31",
        ))
        self.assertTrue(controller.save())
        return controller.selected_evidence

    def test_uses_management_service_selection_and_notification_center(self):
        self.assertIsInstance(
            self.controller.session.evidence_service,
            EvidenceManagementService,
        )

        created = self._create_evidence()

        selection = self.window.selection_store.snapshot.selection
        self.assertIs(selection.identity.kind, SelectionKind.EVIDENCE)
        self.assertEqual(selection.identity.identifier, created.id)
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.SUCCESS,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Evidência criada com sucesso.",
        )

    def test_edit_persists_and_reopen_preserves_all_attributes(self):
        created = self._create_evidence()
        controller = self.controller.evidence_controller
        controller.update_draft(EvidenceDraft(
            evidence_id=created.id,
            document_identity=created.document_identity,
            page_number=2,
            title="Portaria atualizada",
            source_snippet="Trecho atualizado.",
            user_notes="Nota atualizada.",
            category="Administração",
            start_date="2024-02-01",
            end_date="2025-01-31",
        ))
        self.assertTrue(controller.save())

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        self.controller.show_evidences()

        reopened = self.controller.session.evidence_service.get(created.id)
        self.assertEqual(reopened.id, created.id)
        self.assertEqual(reopened.document_identity, created.document_identity)
        self.assertEqual(reopened.page_number, 2)
        self.assertEqual(reopened.title, "Portaria atualizada")
        self.assertEqual(reopened.source_snippet, "Trecho atualizado.")
        self.assertEqual(reopened.user_notes, "Nota atualizada.")
        self.assertEqual(reopened.category, "Administração")
        self.assertEqual(reopened.start_date, "2024-02-01")
        self.assertEqual(reopened.end_date, "2025-01-31")
        self.assertEqual(
            len(self.controller.session.evidence_service.list_all()),
            1,
        )

    def test_pending_removal_policy_preserves_evidence(self):
        created = self._create_evidence()
        workspace = self.window.evidence_workspace

        self.assertFalse(workspace.delete_button.isEnabled())
        self.assertFalse(self.controller.evidence_controller.delete())
        self.assertIsNotNone(
            self.controller.session.evidence_service.get(created.id)
        )
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.INFO,
        )
        self.assertIn(
            "política de retenção",
            self.notifications[-1].message,
        )

    def test_cancel_and_persistence_failure_are_reported(self):
        controller = self.controller.evidence_controller
        controller.start_create()
        controller.update_draft(EvidenceDraft(
            document_identity=self.document.sha256,
            title="Rascunho",
        ))
        controller.cancel()
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

        created = self._create_evidence()
        controller.update_draft(EvidenceDraft(
            evidence_id=created.id,
            document_identity=created.document_identity,
            title="Não persistir",
        ))
        with patch.object(
            controller.service,
            "update",
            side_effect=EvidenceServiceError("SQLite indisponível"),
        ):
            self.assertFalse(controller.save())
        self.assertTrue(controller.dirty)
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )

    def test_list_search_and_sort_use_consolidated_attributes(self):
        first = self._create_evidence()
        controller = self.controller.evidence_controller
        controller.start_create()
        controller.update_draft(EvidenceDraft(
            document_identity=self.document.sha256,
            title="Ata de reunião",
            category="Colegiado",
        ))
        self.assertTrue(controller.save())

        evidence_list = self.window.evidence_workspace.list_widget
        evidence_list.filter_edit.setText("coordenação")
        self.assertEqual(evidence_list.visible_count(), 1)
        self.assertEqual(
            evidence_list.list_widget.item(0)
            .data(Qt.ItemDataRole.UserRole).id,
            first.id,
        )
        evidence_list.filter_edit.clear()
        evidence_list.sort_combo.setCurrentIndex(
            evidence_list.sort_combo.findData("title_asc")
        )
        self.assertTrue(
            evidence_list.list_widget.item(0).text().startswith("Ata")
        )

    def test_inspector_shows_complete_document_origin(self):
        created = self._create_evidence()
        origin = self.window.evidence_workspace.source_status_widget

        self.assertEqual(
            origin.document_label.text(),
            created.document_identity,
        )
        self.assertEqual(origin.page_label.text(), "1")
        self.assertEqual(
            origin.snippet_label.text(),
            "Designar a comissão.",
        )
        self.assertIn("disponível", origin.label.text())
        self.assertEqual(
            origin.checked_at_label.text(),
            "Não registrada",
        )

    def test_open_document_selects_existing_page_and_notifies(self):
        self._create_evidence()

        self.window.evidence_workspace.open_document_button.click()
        self.app.processEvents()

        self.assertIs(
            self.window.stack.currentWidget(),
            self.window.documents_workspace,
        )
        self.assertEqual(
            self.controller.documents_controller.selected_identity,
            self.document.sha256,
        )
        self.assertEqual(
            self.controller.documents_controller.selected_page_number,
            1,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Documento aberto.",
        )

    def test_missing_page_opens_document_and_notifies(self):
        controller = self.controller.evidence_controller
        controller.start_create()
        controller.update_draft(EvidenceDraft(
            document_identity=self.document.sha256,
            page_number=99,
            title="Página histórica",
            source_snippet="Trecho preservado.",
        ))
        self.assertTrue(controller.save())

        self.window.evidence_workspace.open_document_button.click()
        self.app.processEvents()

        self.assertIs(
            self.window.stack.currentWidget(),
            self.window.documents_workspace,
        )
        self.assertEqual(
            self.controller.documents_controller.selected_identity,
            self.document.sha256,
        )
        self.assertIsNone(
            self.controller.documents_controller.selected_page_number
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Página inexistente. Documento aberto.",
        )

    def test_unavailable_source_preserves_identity_and_notifies(self):
        created = self._create_evidence()
        stored = self.project_path / self.document.relative_path
        stored.unlink()
        controller = self.controller.evidence_controller
        controller.load()
        controller.select(created.id)

        self.assertIn(
            "indisponível",
            self.window.evidence_workspace
            .source_status_widget.label.text(),
        )
        self.assertFalse(controller.request_document_navigation())
        self.assertEqual(
            self.notifications[-1].message,
            "Documento indisponível.",
        )
        preserved = self.controller.session.evidence_service.get(created.id)
        self.assertEqual(preserved.id, created.id)
        self.assertEqual(
            preserved.document_identity,
            created.document_identity,
        )


if __name__ == "__main__":
    unittest.main()
