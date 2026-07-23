import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from contracts import DocumentNavigationRequest
from controllers.documents_controller import DocumentsController
from controllers.evidence_controller import EvidenceController
from models import EvidenceSourceCandidate


ROOT = Path(__file__).resolve().parents[1]


class SignalDouble:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        return [callback(*args) for callback in self.callbacks]


class DocumentsWorkspaceDouble:
    def __init__(self):
        self.document_selected = SignalDouble()
        self.page_selected = SignalDouble()
        self.create_evidence_requested = SignalDouble()
        self.details = None
        self.current_page = None


class EvidenceWorkspaceDouble:
    def __init__(self):
        for name in (
            "new_requested", "save_requested", "cancel_requested",
            "delete_requested", "refresh_requested", "evidence_selected",
            "draft_changed", "open_document_requested",
        ):
            setattr(self, name, SignalDouble())

    def clear(self):
        pass

    def set_editor_state(self, *_args):
        pass

    def show_message(self, _message):
        pass


class ModuleIntegrationFlowTests(unittest.TestCase):
    def test_documents_produces_only_neutral_candidate_data(self):
        workspace = DocumentsWorkspaceDouble()
        received = []
        controller = DocumentsController(
            workspace, evidence_source_requested=received.append
        )
        controller.selected_identity = "opaque-document-id"
        workspace.details = SimpleNamespace(
            summary=SimpleNamespace(name="Documento administrativo")
        )
        workspace.current_page = SimpleNamespace(
            page_number=7, text="Trecho documental"
        )

        workspace.create_evidence_requested.emit()

        self.assertEqual(len(received), 1)
        candidate = received[0]
        self.assertIsInstance(candidate, EvidenceSourceCandidate)
        self.assertEqual(candidate.document_identity, "opaque-document-id")
        self.assertEqual(candidate.document_name, "Documento administrativo")
        self.assertEqual(candidate.page_number, 7)
        self.assertEqual(candidate.source_snippet, "Trecho documental")
        self.assertIsNone(candidate.document_path)
        self.assertIsNone(candidate.document_type)
        self.assertIsNone(candidate.search_term)

    def test_evidence_emits_document_navigation_request(self):
        workspace = EvidenceWorkspaceDouble()
        received = []
        controller = EvidenceController(
            workspace, document_navigation_requested=received.append
        )
        controller.selected_evidence = SimpleNamespace(
            document_identity="opaque-document-id", page_number=4
        )

        workspace.open_document_requested.emit()

        self.assertEqual(
            received, [DocumentNavigationRequest("opaque-document-id", 4)]
        )

    def test_forbidden_cross_module_imports_are_absent(self):
        documents_source = (
            ROOT / "controllers" / "documents_controller.py"
        ).read_text(encoding="utf-8")
        evidence_source = (
            ROOT / "controllers" / "evidence_controller.py"
        ).read_text(encoding="utf-8")
        documents_tree = ast.parse(documents_source)
        evidence_tree = ast.parse(evidence_source)

        def imports(tree):
            return {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            } | {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }

        self.assertNotIn("services.evidence_service", imports(documents_tree))
        self.assertNotIn("controllers.documents_controller", imports(evidence_tree))
        self.assertFalse(any(name.startswith("ui.") for name in imports(evidence_tree)))
        self.assertNotIn("EvidenceService", documents_source)
        self.assertNotIn("DocumentsController", evidence_source)


if __name__ == "__main__":
    unittest.main()
