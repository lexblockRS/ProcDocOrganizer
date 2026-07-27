from pathlib import Path
from types import SimpleNamespace
import ast
import unittest

from models.project import Project
from presentation.dashboard import DashboardService, DashboardState


def summary(status, pages=0, valid=False):
    return SimpleNamespace(
        processing_status=status,
        page_count=pages,
        has_processing_result=valid,
    )


def session(documents=(), evidence_count=0, rsc_session=None):
    project = Project(
        project_name="Projeto",
        project_path=Path("projeto.pdop"),
        created_at="2026-01-01T10:00:00",
        last_opened_at="2026-01-02T10:00:00",
    )
    return SimpleNamespace(
        project=project,
        application=None,
        document_service=SimpleNamespace(
            list_documents=lambda: tuple(documents)
        ),
        evidence_service=SimpleNamespace(count=lambda: evidence_count),
        rsc_session=rsc_session,
    )


class DashboardServiceTests(unittest.TestCase):
    def test_empty_project(self):
        projection = DashboardService(session()).build()
        self.assertEqual(projection.state, DashboardState.READY)
        self.assertEqual(projection.documents.total_documents, 0)
        self.assertEqual(projection.evidences.total_evidences, 0)

    def test_aggregates_statuses_and_valid_result_pages(self):
        documents = (
            summary("processed", 5, True),
            summary("pending", 7, False),
            summary("not_processed", 4, False),
            summary("ocr_required", 0, True),
            summary("failed", 3, True),
        )
        result = DashboardService(session(documents)).build().documents
        self.assertEqual(result.total_documents, 5)
        self.assertEqual(result.processed_documents, 1)
        self.assertEqual(result.pending_documents, 2)
        self.assertEqual(result.ocr_required_documents, 1)
        self.assertEqual(result.failed_documents, 1)
        self.assertEqual(result.processed_pages, 8)

    def test_uses_evidence_count(self):
        projection = DashboardService(
            session(evidence_count=4)
        ).build()
        self.assertEqual(projection.evidences.total_evidences, 4)

    def test_service_does_not_access_application_session(self):
        active = session()
        active.rsc_session = property(
            lambda self: (_ for _ in ()).throw(
                AssertionError("application session accessed")
            )
        )

        projection = DashboardService(active).build()

        self.assertEqual(projection.state, DashboardState.READY)

    def test_service_failure_is_propagated(self):
        active = session()
        active.document_service.list_documents = (
            lambda: (_ for _ in ()).throw(RuntimeError("falha"))
        )
        with self.assertRaises(RuntimeError):
            DashboardService(active).build()

    def test_evidence_failure_is_propagated(self):
        active = session()
        active.evidence_service.count = (
            lambda: (_ for _ in ()).throw(RuntimeError("falha"))
        )
        with self.assertRaises(RuntimeError):
            DashboardService(active).build()

    def test_does_not_access_repositories_or_sqlite(self):
        source = (
            Path(__file__).parents[1]
            / "presentation"
            / "dashboard"
            / "service.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("sqlite3", names)
        self.assertFalse(any("Repository" in name for name in names))
        self.assertNotIn("document_repository", source)
        self.assertNotIn("evidence_repository", source)


if __name__ == "__main__":
    unittest.main()
