from types import SimpleNamespace
import unittest

from presentation.dashboard import (
    DashboardController,
    DashboardProjection,
    DashboardState,
)


class ViewSpy:
    def __init__(self):
        self.projections = []

    def set_projection(self, projection):
        self.projections.append(projection)


class ServiceStub:
    def __init__(self, session):
        self.session = session
        self.build_count = 0

    def project_summary(self):
        return SimpleNamespace(project_name=self.session.name)

    def build(self):
        self.build_count += 1
        if getattr(self.session, "fails", False):
            raise RuntimeError("detalhe interno")
        return DashboardProjection(state=DashboardState.READY)


class DashboardControllerTests(unittest.TestCase):
    def setUp(self):
        self.view = ViewSpy()
        self.controller = DashboardController(
            self.view, service_factory=ServiceStub
        )

    def test_initial_state_has_no_project(self):
        self.assertEqual(
            self.view.projections[-1].state,
            DashboardState.NO_PROJECT,
        )

    def test_session_presents_loading_before_ready(self):
        self.assertTrue(self.controller.set_session(
            SimpleNamespace(name="Projeto")
        ))
        self.assertEqual(
            [item.state for item in self.view.projections[-2:]],
            [DashboardState.LOADING, DashboardState.READY],
        )

    def test_refresh_rebuilds_projection(self):
        self.controller.set_session(SimpleNamespace(name="Projeto"))
        service = self.controller._service
        self.controller.refresh()
        self.assertEqual(service.build_count, 2)

    def test_failure_is_controlled(self):
        accepted = self.controller.set_session(
            SimpleNamespace(name="Projeto", fails=True)
        )
        self.assertFalse(accepted)
        self.assertEqual(
            self.view.projections[-1].state,
            DashboardState.ERROR,
        )
        self.assertNotIn(
            "detalhe interno",
            self.view.projections[-1].error_message,
        )

    def test_clear_removes_session_data(self):
        self.controller.set_session(SimpleNamespace(name="Projeto"))
        self.controller.clear_session()
        self.assertIsNone(self.controller._service)
        self.assertEqual(
            self.view.projections[-1].state,
            DashboardState.NO_PROJECT,
        )

    def test_switch_replaces_service_without_leaking_session(self):
        first = SimpleNamespace(name="A")
        second = SimpleNamespace(name="B")
        self.controller.set_session(first)
        self.controller.set_session(second)
        self.assertIs(self.controller._service.session, second)


if __name__ == "__main__":
    unittest.main()
