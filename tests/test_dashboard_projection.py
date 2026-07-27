from dataclasses import FrozenInstanceError
import unittest

from presentation.dashboard import (
    DashboardProjection,
    DashboardState,
)


class DashboardProjectionTests(unittest.TestCase):
    def test_defaults_represent_no_project(self):
        projection = DashboardProjection()
        self.assertEqual(projection.state, DashboardState.NO_PROJECT)
        self.assertIsNone(projection.project)
        self.assertEqual(projection.documents.total_documents, 0)
        self.assertEqual(projection.evidences.total_evidences, 0)

    def test_projections_are_immutable(self):
        projection = DashboardProjection()
        with self.assertRaises(FrozenInstanceError):
            projection.state = DashboardState.READY

if __name__ == "__main__":
    unittest.main()
