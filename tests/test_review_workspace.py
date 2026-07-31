import unittest

from PySide6.QtWidgets import QApplication
from applications.rsc.review_workspace_view_model import ReviewWorkspaceViewModel
from applications.rsc.services.review_workspace_service import ReviewWorkspaceService
from tests.test_review_workspace_service import sources
from ui.review_workspace import ReviewWorkspaceView


class ReviewWorkspaceViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_emits_item_navigation_intent(self):
        data = ReviewWorkspaceViewModel(ReviewWorkspaceService().compose(*sources())).data
        view = ReviewWorkspaceView(data)
        emitted = []
        view.navigation_requested.connect(emitted.append)
        view.items_list.setCurrentRow(0)
        view.open_button.click()
        self.assertEqual(emitted, [data.items[0].navigation_intent])

    def test_emits_filter_contract_without_filtering_locally(self):
        data = ReviewWorkspaceViewModel(ReviewWorkspaceService().compose(*sources())).data
        view = ReviewWorkspaceView(data)
        emitted = []
        view.navigation_requested.connect(emitted.append)
        view.pending_filter.setChecked(True)
        view.apply_filters_button.click()
        self.assertTrue(any(item.filter_id == "review.only_pending" for item in emitted[0].filters))
        self.assertEqual(view.data, data)


if __name__ == "__main__":
    unittest.main()
