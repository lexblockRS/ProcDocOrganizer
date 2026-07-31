from dataclasses import FrozenInstanceError
import unittest

from applications.rsc.review_workspace_view_model import ReviewWorkspaceViewModel
from applications.rsc.services.review_workspace_service import ReviewWorkspaceService
from tests.test_review_workspace_service import sources


class ReviewWorkspaceViewModelTests(unittest.TestCase):
    def test_projects_only_immutable_presentation_data(self):
        data = ReviewWorkspaceViewModel(ReviewWorkspaceService().compose(*sources())).data
        self.assertEqual(data.summary.project_name, "Processo")
        self.assertTrue(data.items[0].navigation_intent)
        with self.assertRaises(FrozenInstanceError):
            data.workspace_revision = 9  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
