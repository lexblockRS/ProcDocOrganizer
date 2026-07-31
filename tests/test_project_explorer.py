from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import ast
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from applications import RscApplication
from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from core.application_registry import ApplicationRegistry
from platform_sdk import Document, ProjectState
from ui.project_explorer import ProjectExplorerWindow


class ProjectExplorerWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "projects.sqlite"
        self.workspace_base = self.root / "workspaces"
        self.registry = ApplicationRegistry((RscApplication(),))
        self.window = self._window()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temporary_directory.cleanup()

    def _window(self) -> ProjectExplorerWindow:
        return ProjectExplorerWindow(
            database_path=self.database_path,
            workspace_base=self.workspace_base,
            application_registry=self.registry,
        )

    def test_window_contains_only_project_actions_and_information(self):
        menu_titles = tuple(
            action.text() for action in self.window.menuBar().actions()
        )

        self.assertEqual(menu_titles, ("Arquivo", "Ajuda"))
        self.assertEqual(self.window.name_value.text(), "—")
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Nenhum projeto aberto.",
        )
        self.assertFalse(self.window.action_close.isEnabled())
        self.assertEqual(self.window.evidence_list.count(), 0)
        self.assertFalse(self.window.add_evidence_button.isEnabled())

    def test_create_close_and_reopen_after_application_restart(self):
        created = self.window.create_project(
            name="Projeto do usuário",
            application_id="rsc",
        )
        aggregate_id = created.aggregate_id
        workspace_root = self.window.current_workspace.root

        self.assertTrue(workspace_root.is_dir())
        self.assertEqual(self.window.name_value.text(), created.name)
        self.assertEqual(
            self.window.aggregate_id_value.text(),
            aggregate_id,
        )
        self.assertEqual(self.window.application_value.text(), "rsc")
        self.assertEqual(
            self.window.state_value.text(),
            ProjectState.DRAFT.value,
        )
        self.assertEqual(self.window.revision_value.text(), "0")
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Projeto salvo.",
        )

        self.window.close_project()
        self.assertIsNone(self.window.current_project)
        self.assertTrue(workspace_root.is_dir())
        self.assertEqual(self.window.name_value.text(), "—")

        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.window = self._window()
        reopened = self.window.open_project_by_id(aggregate_id)

        self.assertEqual(reopened.aggregate_id, aggregate_id)
        self.assertEqual(reopened.state, created.state)
        self.assertEqual(reopened.revision, created.revision)
        self.assertEqual(reopened.application_id, created.application_id)
        self.assertEqual(
            self.window.current_workspace.root,
            workspace_root,
        )
        self.assertEqual(
            self.window.workspace_value.text(),
            str(workspace_root),
        )
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Projeto carregado.",
        )

    def test_close_project_does_not_delete_database_or_workspace(self):
        created = self.window.create_project(
            name="Projeto persistente",
            application_id="rsc",
        )
        workspace_root = self.window.current_workspace.root

        self.window.close_project()
        reopened = self.window.open_project_by_id(created.aggregate_id)

        self.assertEqual(reopened.aggregate_id, created.aggregate_id)
        self.assertTrue(self.database_path.is_file())
        self.assertTrue(workspace_root.is_dir())

    def test_evidence_crud_is_scoped_to_current_project(self):
        self.window.create_project(
            name="Projeto com evidências",
            application_id="rsc",
        )

        created = self.window.create_evidence(title="Portaria")
        self.assertEqual(self.window.evidence_list.count(), 1)
        self.assertEqual(
            self.window.evidence_list.item(0).data(
                Qt.ItemDataRole.UserRole
            ),
            created.aggregate_id,
        )

        updated = self.window.edit_evidence(
            created.aggregate_id,
            title="Portaria atualizada",
        )
        self.assertTrue(updated.same_evidence(created))
        self.assertEqual(
            self.window.evidence_list.item(0).text(),
            "Portaria atualizada",
        )

        self.window.remove_evidence(created.aggregate_id)
        self.assertEqual(self.window.evidence_list.count(), 0)

    def test_evidence_is_reloaded_with_project(self):
        project = self.window.create_project(
            name="Projeto reaberto",
            application_id="rsc",
        )
        evidence = self.window.create_evidence(title="Certidão")

        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.window = self._window()
        self.window.open_project_by_id(project.aggregate_id)

        self.assertEqual(self.window.evidence_list.count(), 1)
        item = self.window.evidence_list.item(0)
        self.assertEqual(item.text(), "Certidão")
        self.assertEqual(
            item.data(Qt.ItemDataRole.UserRole),
            evidence.aggregate_id,
        )

    def test_execution_facts_follow_selected_evidence_and_reopen(self):
        project = self.window.create_project(
            name="Projeto factual",
            application_id="rsc",
        )
        first_evidence = self.window.create_evidence(title="Portaria")
        first_fact = self.window.create_execution_fact(
            fact_type="DESIGNACAO",
            description="Designação original",
            quantity=Decimal("1"),
            unit="evento",
        )
        second_evidence = self.window.create_evidence(title="Certidão")

        self.assertEqual(self.window.execution_fact_list.count(), 0)
        self.window.evidence_list.setCurrentRow(0)
        self.assertEqual(self.window.execution_fact_list.count(), 1)

        updated = self.window.edit_execution_fact(
            first_fact.aggregate_id,
            description="Designação atualizada",
        )
        self.assertTrue(updated.same_execution_fact(first_fact))
        self.assertIn(
            "Designação atualizada",
            self.window.execution_fact_list.item(0).text(),
        )

        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.window = self._window()
        self.window.open_project_by_id(project.aggregate_id)
        self.window.evidence_list.setCurrentRow(0)

        self.assertEqual(self.window.execution_fact_list.count(), 1)
        self.assertEqual(
            self.window.execution_fact_list.item(0).data(
                Qt.ItemDataRole.UserRole
            ),
            first_fact.aggregate_id,
        )
        self.assertNotEqual(
            first_evidence.aggregate_id,
            second_evidence.aggregate_id,
        )

    def test_execution_fact_can_be_removed(self):
        self.window.create_project(
            name="Projeto factual",
            application_id="rsc",
        )
        self.window.create_evidence(title="Portaria")
        fact = self.window.create_execution_fact(
            fact_type="ATIVIDADE",
            description="Atividade",
            quantity=Decimal("2"),
            unit="atividade",
        )

        self.window.remove_execution_fact(fact.aggregate_id)

        self.assertEqual(self.window.execution_fact_list.count(), 0)

    def test_execution_binding_uses_catalog_and_preserves_fact(self):
        self.window.create_project(
            name="Projeto com enquadramento",
            application_id="rsc",
        )
        self.window.create_evidence(title="Portaria")
        fact = self.window.create_execution_fact(
            fact_type="DESIGNACAO",
            description="Designação",
            quantity=Decimal("1"),
            unit="evento",
        )
        first = OFFICIAL_NORMATIVE_CATALOG.criteria[0]
        second = OFFICIAL_NORMATIVE_CATALOG.criteria[1]

        binding = self.window.create_binding(criterion_id=first.code)
        updated = self.window.rebind_execution_fact(
            criterion_id=second.code
        )

        self.assertTrue(updated.same_binding(binding))
        self.assertEqual(updated.criterion_id, second.code)
        self.assertIn(second.code, self.window.binding_value.text())
        self.assertEqual(
            self.window._service.get_fact(fact.aggregate_id),
            fact,
        )

        self.window.remove_selected_binding()
        self.assertEqual(self.window.binding_value.text(), "—")

    def test_execute_evaluation_shows_summary(self):
        self.window.create_project(
            name="Projeto executável",
            application_id="rsc",
        )
        evidence = self.window.create_evidence(title="Ata")
        self.window._service.attach_document(
            evidence.aggregate_id,
            project_id=self.window.current_project.aggregate_id,
            document=Document(
                document_id="ata-documento",
                name="ata.pdf",
                relative_path="documents/ata.pdf",
                document_type="application/pdf",
            ),
        )
        self.window.create_execution_fact(
            fact_type="PARTICIPACAO_EVENTO",
            description="Três participações",
            quantity=Decimal("3"),
            unit="Por evento",
        )
        self.window.create_binding(
            criterion_id="DEC13048-ANX-II-ITEM-07"
        )

        result = self.window.execute_evaluation()

        self.assertEqual(result.total_score, Decimal("9"))
        self.assertIn("CriterionScores: 1", self.window.execution_summary.text())
        self.assertIn("Pontuação: 9", self.window.execution_summary.text())
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Avaliação concluída.",
        )
        results_view = self.window.open_results()
        self.assertEqual(results_view.summary.total_score, Decimal("9"))
        self.assertEqual(
            results_view.results_tree.topLevelItemCount(), 1
        )
        self.assertTrue(self.window.view_results_button.isEnabled())
        self.assertTrue(self.window.view_report_button.isEnabled())
        report_view = self.window.open_evaluation_report()
        self.assertEqual(report_view.report.total_score, Decimal("9"))
        self.assertEqual(report_view.tabs.count(), 5)

    def test_ui_uses_application_service_without_database_imports(self):
        path = Path(__file__).parents[1] / "ui" / "project_explorer.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(any(
            item == "database" or item.startswith("database.")
            for item in imports
        ))
        self.assertIn(
            "applications.rsc.project_explorer_composition", imports
        )


if __name__ == "__main__":
    unittest.main()
