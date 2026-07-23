import unittest
from types import SimpleNamespace

from core.project_controller import ProjectController


class EvidenceControllerSpy:
    def __init__(self, result, calls):
        self.result = result
        self.calls = calls

    def start_create(self):
        self.calls.append("start_create")
        return self.result

    def start_create_from_source(self, _candidate):
        self.calls.append("start_create_from_source")
        return self.result


class WindowSpy:
    def __init__(self, calls):
        self.calls = calls
        self.search_workspace = SimpleNamespace(show_message=lambda _message: None)

    def show_evidences(self):
        self.calls.append("navigate")

    def show_documents(self):
        self.calls.append("navigate_documents")


class ProjectControllerEvidenceNavigationTests(unittest.TestCase):
    def controller(self, result):
        calls = []
        controller = ProjectController.__new__(ProjectController)
        controller.state = SimpleNamespace(has_project=True)
        controller.window = WindowSpy(calls)
        controller.evidence_controller = EvidenceControllerSpy(result, calls)
        return controller, calls

    def test_manual_creation_confirms_before_navigation(self):
        controller, calls = self.controller(True)
        controller.new_evidence()
        self.assertEqual(calls, ["start_create", "navigate"])

    def test_manual_creation_cancel_or_save_failure_does_not_navigate(self):
        controller, calls = self.controller(False)
        controller.new_evidence()
        self.assertEqual(calls, ["start_create"])

    def test_search_creation_was_already_ordered_correctly(self):
        controller, calls = self.controller(True)
        self.assertTrue(controller._create_evidence_from_search(object()))
        self.assertEqual(calls, ["start_create_from_source", "navigate"])

        controller, calls = self.controller(False)
        self.assertFalse(controller._create_evidence_from_search(object()))
        self.assertEqual(calls, ["start_create_from_source"])

    def test_documents_navigation_checks_dirty_before_refresh_and_navigation(self):
        controller, calls = self.controller(True)
        controller.evidence_controller.can_leave = lambda: calls.append("can_leave") or True
        controller.documents_controller = SimpleNamespace(
            refresh=lambda: calls.append("refresh") or True
        )
        controller.show_documents()
        self.assertEqual(calls, ["can_leave", "refresh", "navigate_documents"])

    def test_documents_navigation_cancel_preserves_current_workspace(self):
        controller, calls = self.controller(True)
        controller.evidence_controller.can_leave = lambda: calls.append("can_leave") or False
        controller.documents_controller = SimpleNamespace(
            refresh=lambda: calls.append("refresh")
        )
        controller.show_documents()
        self.assertEqual(calls, ["can_leave"])

    def test_search_document_navigation_refreshes_then_navigates_then_shows(self):
        controller, calls = self.controller(True)
        controller.evidence_controller.can_leave = (
            lambda: calls.append("can_leave") or True
        )
        controller.documents_controller = SimpleNamespace(
            refresh=lambda: calls.append("refresh") or True,
            navigate=lambda request: calls.append(("navigate_request", request))
            or True,
        )
        request = object()
        self.assertTrue(controller._navigate_from_search(request))
        self.assertEqual(
            calls,
            [
                "can_leave",
                "refresh",
                ("navigate_request", request),
                "navigate_documents",
            ],
        )

    def test_search_document_navigation_stops_on_refresh_or_resolution_failure(self):
        controller, calls = self.controller(True)
        controller.evidence_controller.can_leave = (
            lambda: calls.append("can_leave") or True
        )
        controller.documents_controller = SimpleNamespace(
            refresh=lambda: calls.append("refresh") or False,
            navigate=lambda _request: calls.append("navigate") or True,
        )
        self.assertFalse(controller._navigate_from_search(object()))
        self.assertEqual(calls, ["can_leave", "refresh"])

    def test_evidence_document_navigation_uses_same_documents_route(self):
        controller, calls = self.controller(True)
        controller.evidence_controller.can_leave = (
            lambda: calls.append("can_leave") or True
        )
        controller.documents_controller = SimpleNamespace(
            refresh=lambda: calls.append("refresh") or True,
            navigate=lambda request: calls.append(("navigate_request", request))
            or True,
        )
        request = object()

        self.assertTrue(controller._navigate_from_evidence(request))
        self.assertEqual(
            calls,
            [
                "can_leave",
                "refresh",
                ("navigate_request", request),
                "navigate_documents",
            ],
        )

    def test_documents_creation_prepares_evidence_then_shows_workspace(self):
        controller, calls = self.controller(True)
        controller.window.documents_workspace = SimpleNamespace(
            show_message=lambda message: calls.append(("message", message))
        )
        candidate = object()

        self.assertTrue(controller._create_evidence_from_documents(candidate))
        self.assertEqual(calls, ["start_create_from_source", "navigate"])


if __name__ == "__main__":
    unittest.main()
